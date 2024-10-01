from transformers import VisionEncoderDecoderConfig, DonutProcessor, VisionEncoderDecoderModel
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import EarlyStopping
from datasets.exceptions import DatasetNotFoundError
from nltk import edit_distance
from torch.utils.data import DataLoader
from PyLib.donut_model.donut_upload import PushToHubCallback
from PyLib.donut_model.donut_dataset_input import DonutDatasetInput
import pytorch_lightning as pl
import logging
import re
import numpy as np
import torch

class DonutModelPLModule(pl.LightningModule):
    def __init__(self, config, processor, model, max_length, train_dataset, val_dataset):
        super().__init__()
        self.config = config
        self.processor = processor
        self.model = model
        self.max_length = max_length
        # feel free to increase the batch size if you have a lot of memory
        # I'm fine-tuning on Colab and given the large image size, batch size > 1 is not feasible
        self.stored_train_dataloader = DataLoader(train_dataset, batch_size=1, shuffle=True, num_workers=4, persistent_workers=True)
        self.stored_val_dataloader = DataLoader(val_dataset, batch_size=1, shuffle=False, num_workers=4, persistent_workers= True)
        print("Train dataloader: ", len(self.stored_train_dataloader))
        print("Validation dataloader: ", len(self.stored_val_dataloader))

    def training_step(self, batch, batch_idx):
        pixel_values, labels, _ = batch
        
        outputs = self.model(pixel_values, labels=labels)
        loss = outputs.loss
        self.log("train_loss", loss, batch_size=pixel_values.size(0))
        return loss

    def validation_step(self, batch, batch_idx, dataset_idx=0):
        pixel_values, labels, answers = batch
        batch_size = pixel_values.shape[0]
        # we feed the prompt to the model
        decoder_input_ids = torch.full((batch_size, 1), self.model.config.decoder_start_token_id, device=self.device)
        
        outputs = self.model.generate(pixel_values,
                                   decoder_input_ids=decoder_input_ids,
                                   max_length=self.max_length,
                                   early_stopping=False,
                                   pad_token_id=self.processor.tokenizer.pad_token_id,
                                   eos_token_id=self.processor.tokenizer.eos_token_id,
                                   use_cache=True,
                                   num_beams=1,
                                   bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                                   return_dict_in_generate=True,)
    
        predictions = []
        for seq in self.processor.tokenizer.batch_decode(outputs.sequences):
            seq = seq.replace(self.processor.tokenizer.eos_token, "").replace(self.processor.tokenizer.pad_token, "")
            seq = re.sub(r"<.*?>", "", seq, count=1).strip()  # remove first task start token
            predictions.append(seq)

        scores = []
        for pred, answer in zip(predictions, answers):
            pred = re.sub(r'(?:(?<=>)\s|(?=\s<))', '', pred, count=1)
            answer = answer.replace(self.processor.tokenizer.eos_token, "")
            scores.append(edit_distance(pred, answer) / max(len(pred), len(answer)))

            if self.config.get("verbose", False) and len(scores) == 1:
                print(f"Prediction: {pred}")
                print(f"    Answer: {answer}")
                print(f" Normed ED: {scores[0]}")

        self.log("val_edit_distance", np.mean(scores), batch_size=pixel_values.size(0))
        
        return scores

    def configure_optimizers(self):
        # you could also add a learning rate scheduler if you want
        optimizer = torch.optim.Adam(self.parameters(), lr=self.config.get("lr"))
    
        return optimizer

    def train_dataloader(self):
        return self.stored_train_dataloader

    def val_dataloader(self):
        return self.stored_val_dataloader
    
class DonutTrainer():
    def __init__(
            self, 
            model_path: str, 
            dataset_path: str, 
            target_path: str, 
            image_resize_width: int, 
            image_resize_height: int, 
            token_sequence_max_length: int,
            device: str,
            precision: int,
            dev_mode: bool = False):
        image_size = [image_resize_width, image_resize_height]

        logging.info("Initializing model trainer")
        # update image_size of the encoder
        # during pre-training, a larger image size was used
        try:
            config = VisionEncoderDecoderConfig.from_pretrained(model_path)
        except OSError:
            logging.error(f"Could not find model config at {model_path}")
            raise
        except Exception as e:
            logging.error(f"Could not initialize model config: {e}")
            raise
        config.encoder.image_size = image_size # (height, width)
        # update max_length of the decoder (for generation)
        config.decoder.max_length = token_sequence_max_length
        # TODO we should actually update max_position_embeddings and interpolate the pre-trained ones:
        # https://github.com/clovaai/donut/blob/0acc65a85d140852b8d9928565f0f6b2d98dc088/donut/model.py#L602
        try:
            processor = DonutProcessor.from_pretrained(model_path)
        except OSError:
            logging.error(f"Could not find processor at {model_path}")
            raise
        except Exception as e:
            logging.error(f"Could not initialize processor: {e}")
            raise
        try:
            model = VisionEncoderDecoderModel.from_pretrained(model_path, config=config)
        except OSError:
            logging.error(f"Could not find model at {model_path}")
            raise
        except Exception as e:
            logging.error(f"Could not initialize model: {e}")
            raise
        # we update some settings which differ from pretraining; namely the size of the images + no rotation required
        # source: https://github.com/clovaai/donut/blob/master/config/train_cord.yaml
        processor.image_processor.size = image_size[::-1] # should be (width, height)
        processor.image_processor.do_align_long_axis = False

        logging.info("Initializing datasets")
        try:
            train_dataset = DonutDatasetInput(dataset_path, max_length=token_sequence_max_length,
                                            processor=processor, model=model,
                                            split="train", task_start_token="<s_cord-v2>", prompt_end_token="<s_cord-v2>",
                                            sort_json_key=False, # cord dataset is preprocessed, so no need for this
                                            )

            val_dataset = DonutDatasetInput(dataset_path, max_length=token_sequence_max_length,
                                            processor=processor, model=model,
                                            split="validation", task_start_token="<s_cord-v2>", prompt_end_token="<s_cord-v2>",
                                            sort_json_key=False, # cord dataset is preprocessed, so no need for this
                                            )
            
            print(len(train_dataset.added_tokens))
            print(len(val_dataset.added_tokens))
            print(train_dataset.added_tokens)
            print(val_dataset.added_tokens)
            print(processor.decode([57560]))
        except DatasetNotFoundError:
            logging.error(f"Could not find dataset at {dataset_path}")
            raise
        except Exception as e:
            logging.error(f"Could not initialize dataset: {e}")
            raise

        model.config.pad_token_id = processor.tokenizer.pad_token_id
        model.config.decoder_start_token_id = processor.tokenizer.convert_tokens_to_ids(['<s_cord-v2>'])[0]
        # sanity check
        print("Pad token ID:", processor.decode([model.config.pad_token_id]))
        print("Decoder start token ID:", processor.decode([model.config.decoder_start_token_id]))

        config = {"max_epochs":30,
            "val_check_interval":0.2, # how many times we want to validate during an epoch
            "check_val_every_n_epoch":1,
            "gradient_clip_val":1.0,
            "num_training_samples_per_epoch": 800,
            "lr":3e-5,
            "train_batch_sizes": [8],
            "val_batch_sizes": [1],
            # "seed":2022,
            "num_nodes": 1,
            "warmup_steps": 300, # 800/8*30/10, 10%
            "result_path": target_path,
            "verbose": True,
            }

        logging.info("Initializing module")
        try:
            self.model_module = DonutModelPLModule(config, processor, model, token_sequence_max_length, train_dataset, val_dataset)
        except Exception as e:
            logging.error(f"Could not initialize model module: {e}")
            raise

        wandb_logger = WandbLogger(project="Donut", name="demo-run-cord")

        early_stop_callback = EarlyStopping(monitor="val_edit_distance", patience=3, verbose=False, mode="min")

        logging.info("Training model")
        try:
            self.trainer = pl.Trainer(
                        accelerator=device,
                        devices=1,
                        max_epochs=config.get("max_epochs"),
                        fast_dev_run=dev_mode,
                        precision=precision,
                        num_sanity_val_steps=0,
                        logger=wandb_logger,
                        callbacks=[PushToHubCallback(target_path), early_stop_callback],
            )
        except Exception as e:
            logging.error(f"Could not initialize trainer: {e}")
            raise

    def run(self):
        try:
            self.trainer.fit(self.model_module)
        except Exception as e:
            logging.error(f"Failed to run trainer: {e}")