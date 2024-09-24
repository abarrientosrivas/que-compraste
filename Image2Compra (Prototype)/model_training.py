from datasets import load_dataset
from transformers import VisionEncoderDecoderConfig, DonutProcessor, VisionEncoderDecoderModel
from typing import Any, List, Tuple
from torch.utils.data import Dataset, DataLoader
from utils import DonutDataset, DonutModelPLModule, PushToHubCallback
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import Callback, EarlyStopping
import json
import random
import torch

from torch.nn.utils.rnn import pad_sequence
from torch.optim.lr_scheduler import LambdaLR

import pytorch_lightning as pl
from pytorch_lightning.utilities import rank_zero_only

image_size = [1280, 960]
max_length = 768

def main():
    # update image_size of the encoder
    # during pre-training, a larger image size was used
    config = VisionEncoderDecoderConfig.from_pretrained("naver-clova-ix/donut-base")
    config.encoder.image_size = image_size # (height, width)
    # update max_length of the decoder (for generation)
    config.decoder.max_length = max_length
    # TODO we should actually update max_position_embeddings and interpolate the pre-trained ones:
    # https://github.com/clovaai/donut/blob/0acc65a85d140852b8d9928565f0f6b2d98dc088/donut/model.py#L602
    processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base")
    model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base", config=config)
    # we update some settings which differ from pretraining; namely the size of the images + no rotation required
    # source: https://github.com/clovaai/donut/blob/master/config/train_cord.yaml
    processor.image_processor.size = image_size[::-1] # should be (width, height)
    processor.image_processor.do_align_long_axis = False

    train_dataset = DonutDataset("naver-clova-ix/cord-v2", max_length=max_length,
                                split="train", task_start_token="", prompt_end_token="",
                                sort_json_key=False, # cord dataset is preprocessed, so no need for this
                                )

    val_dataset = DonutDataset("naver-clova-ix/cord-v2", max_length=max_length,
                                split="validation", task_start_token="", prompt_end_token="",
                                sort_json_key=False, # cord dataset is preprocessed, so no need for this
                                )


    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.decoder_start_token_id = processor.tokenizer.convert_tokens_to_ids([''])[0]

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
          "result_path": "./result",
          "verbose": True,
          }

    model_module = DonutModelPLModule(config, processor, model, max_length, train_dataset, val_dataset)

    wandb_logger = WandbLogger(project="Donut", name="demo-run-cord")

    early_stop_callback = EarlyStopping(monitor="val_edit_distance", patience=3, verbose=False, mode="min")

    trainer = pl.Trainer(
            accelerator="gpu",
            devices=1,
            max_epochs=config.get("max_epochs"),
            val_check_interval=config.get("val_check_interval"),
            check_val_every_n_epoch=config.get("check_val_every_n_epoch"),
            gradient_clip_val=config.get("gradient_clip_val"),
            precision=16, # we'll use mixed precision
            num_sanity_val_steps=0,
            logger=wandb_logger,
            callbacks=[PushToHubCallback(), early_stop_callback],
    )

    trainer.fit(model_module)