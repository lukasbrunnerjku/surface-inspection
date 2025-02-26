import evaluate
from datasets import load_dataset
from torchvision.transforms import (
    CenterCrop,
    Compose,
    Normalize,
    ToTensor,
    RandomHorizontalFlip,
    RandomVerticalFlip,
)
from transformers import (
    AutoModelForImageClassification,
    TrainingArguments,
    Trainer,
    AutoImageProcessor,
)
import numpy as np
import os

os.environ["REQUESTS_CA_BUNDLE"] = r"C:\Users\lbrunn\certs\cacert.crt"
os.environ["SSL_CERT_FILE"] = r"C:\Users\lbrunn\certs\cacert.crt"


def compute_metrics(eval_pred):
    accuracy = evaluate.load("accuracy")
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    return accuracy.compute(predictions=predictions, references=labels)


class Transforms:

    def __init__(self, transforms):
        self.tf = transforms

    def apply_transforms(self, examples: dict):  # Keys: "image", "label"
        examples["pixel_values"] = [self.tf(img.convert("RGB")) for img in examples["image"]]
        del examples["image"]
        return examples
        

def main():
    root = r"C:\Users\lbrunn\projects\surface-inspection\datasets\wood"
    size = 128
    mean = 0.5
    std = 0.5
    test_fraction = 0.1
    pretrained_model_name_or_path = "google/mobilenet_v2_1.0_224"
    output_dir = r"C:\Users\lbrunn\projects\surface-inspection\classify\logs"
    learning_rate = 1e-3
    num_train_epochs = 10
    seed = 42
    num_workers = 0
    batch_size = 64
    skip_training = True

    if skip_training:  # Evaluation on test set only.
        """
        This checkpoint has 1.0 accuracy on train/val set and 0.9934375 on test set.
        """
        pretrained_model_name_or_path = r"C:\Users\lbrunn\projects\surface-inspection\classify\logs\checkpoint-1350"

    train_transforms = Transforms(Compose([
        CenterCrop(size),
        RandomHorizontalFlip(),
        RandomVerticalFlip(),
        ToTensor(),
        Normalize(mean, std),
    ]))

    test_transforms = Transforms(Compose([
        CenterCrop(size),
        ToTensor(),
        Normalize(mean, std),
    ]))

    loaded = load_dataset("imagefolder", data_dir=root)
    train_ds = loaded["train"]
    test_ds = loaded["test"]
    val_ds = train_ds.train_test_split(
        test_size=test_fraction,
        shuffle=True,  # Keep True for stratified splitting.
        stratify_by_column="label",
    )  # Stratified; Keeps the same label distribution in each split.

    train_ds = train_ds.with_transform(train_transforms.apply_transforms)
    test_ds = test_ds.with_transform(test_transforms.apply_transforms)
    val_ds = val_ds.with_transform(test_transforms.apply_transforms)

    labels = train_ds.features["label"].names
    label2id, id2label = dict(), dict()
    for i, label in enumerate(labels):
        label2id[label] = str(i)
        id2label[str(i)] = label

    # NOTE: See with which transformations the model was trained with.
    # image_processor = AutoImageProcessor.from_pretrained(
    #     pretrained_model_name_or_path,
    # )

    model = AutoModelForImageClassification.from_pretrained(
        pretrained_model_name_or_path,
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        remove_unused_columns=False,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=1,
        per_device_eval_batch_size=batch_size,
        num_train_epochs=num_train_epochs,
        warmup_ratio=0.1,
        logging_steps=100,
        load_best_model_at_end=True,
        metric_for_best_model="eval_test_accuracy",
        dataloader_num_workers=num_workers,
        dataloader_drop_last=True,
        dataloader_pin_memory=True,
        # dataloader_persistent_workers=False,  # Keep False or OOM error!
        label_smoothing_factor=0.1,
        seed=seed,
        save_total_limit=3,  # Keep only top 3 checkpoints (including the best one) in logs.
        eval_delay=2,  # Start evaluating after 2 epochs.
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        # processing_class=image_processor,
        compute_metrics=compute_metrics,
    )

    if not skip_training:
        trainer.train()

    print(trainer.evaluate(test_ds, metric_key_prefix="test"))


if __name__ == "__main__":
    main()
