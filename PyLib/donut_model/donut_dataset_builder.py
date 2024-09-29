from pathlib import Path
from datasets import Dataset, DatasetDict
import json
import random
import cv2

def generate_metadata(target_dir: Path, img_dir: Path, files_list, split):
    split_dir = target_dir / split
    split_dir.mkdir(parents=True, exist_ok=True)

    metadata_list = []

    for file_name in files_list:
        img_file = img_dir / f"{file_name.stem}.jpg"
        if img_file.exists():
            img = cv2.imread(str(img_file))
            cv2.imwrite(str(split_dir / f"{file_name.stem}.jpg"), img)

            with open(file_name, "r") as json_file:
                data = json.load(json_file)
                metadata_list.append({
                    "ground_truth": json.dumps({"gt_parse": data}),
                    "file_name": f"{file_name.stem}.jpg"
                })

    with open(split_dir / "metadata.jsonl", "w") as outfile:
        for entry in metadata_list:
            json.dump(entry, outfile)
            outfile.write("\n")

    print(f"Generated metadata for {len(metadata_list)} images in {split} set")

def generate_dataset_dict(data_dir: Path) -> DatasetDict:
    dataset_dict = DatasetDict()
    
    for split in ['train', 'validation', 'test']:
        split_dir = data_dir / split
        metadata_file = split_dir / "metadata.jsonl"
        
        if split_dir.exists() and metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = [json.loads(line) for line in f]
            
            dataset = Dataset.from_dict({
                'image': [str(split_dir / item['file_name']) for item in metadata],
                'ground_truth': [item['ground_truth'] for item in metadata]
            })
            
            dataset_dict[split] = dataset
            print(f"{split.capitalize()} set has {len(dataset)} images")
        else:
            print(f"Directory or metadata file not found for {split} set")
    
    if dataset_dict:
        print(f"Dataset features are: {next(iter(dataset_dict.values())).features.keys()}")
        
        if 'train' in dataset_dict and dataset_dict['train']:
            train_dataset = dataset_dict['train']
            random_sample = random.choice(range(len(train_dataset)))
            print(f"Random sample from training set:")
            print(f"Image path: {train_dataset[random_sample]['image']}")
            print(f"Ground truth: {train_dataset[random_sample]['ground_truth']}")
    else:
        print("No datasets were loaded")

    return dataset_dict

def generate_dataset(json_dir: str, img_dir: str, target_dir: str):
    data_dir_json = Path(json_dir)
    data_dir_img = Path(img_dir)
    target_data_dir = Path (target_dir)

    if not data_dir_json.exists() or not data_dir_img.exists():
        raise FileNotFoundError("Data directories not found")

    json_files = list(data_dir_json.glob("*.json"))
    random.shuffle(json_files)

    # Split files into train, validation, and test sets
    total_files = len(json_files)
    train_size = int(total_files * 0.5)
    val_size = int(total_files * 0.25)
    train_files = json_files[:train_size]
    val_files = json_files[train_size:train_size+val_size]
    test_files = json_files[train_size+val_size:]

    print(f"Train set size: {len(train_files)}")
    print(f"Validation set size: {len(val_files)}")
    print(f"Test set size: {len(test_files)}")

    # Generate metadata
    for split, files in [("train", train_files), ("validation", val_files), ("test", test_files)]:
        generate_metadata(target_data_dir, data_dir_img, files, split)

    # Generate dataset
    datasets = generate_dataset_dict(target_data_dir)

    if datasets:
        print("Datasets generated successfully")
    else:
        print("Failed to generate datasets")