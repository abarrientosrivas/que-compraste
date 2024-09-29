from pytorch_lightning.callbacks import Callback
from datasets import load_dataset

class PushToHubCallback(Callback):
    def __init__(self, target_path: str):
        self.target_path = target_path

    def on_train_epoch_end(self, trainer, pl_module):
        print(f"Pushing model to the hub, epoch {trainer.current_epoch}")
        pl_module.model.push_to_hub(self.target_path,
                                    commit_message=f"Training in progress, epoch {trainer.current_epoch}")

    def on_train_end(self, trainer, pl_module):
        print(f"Pushing model to the hub after training")
        pl_module.processor.push_to_hub(self.target_path,
                                    commit_message=f"Training done")
        pl_module.model.push_to_hub(self.target_path,
                                    commit_message=f"Training done")

def upload_dataset(data_dir: str, dataset_name: str, private: bool = True):
    dataset = load_dataset("imagefolder", data_dir=data_dir)
    dataset.push_to_hub(dataset_name, private=private)
