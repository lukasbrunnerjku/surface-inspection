import sys
sys.path.append(".")

import torch
from transformers.models.mobilenet_v2 import MobileNetV2ForImageClassification
import torch.nn.functional as F
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from tqdm import tqdm

from classify.train import *


if __name__ == "__main__":
    root = r"C:\Users\lbrunn\projects\surface-inspection\datasets\wood"
    size = 128
    mean = 0.5
    std = 0.5
    pretrained_model_name_or_path = r"C:\Users\lbrunn\projects\surface-inspection\classify\logs\checkpoint-1350"

    test_transforms = Transforms(Compose([
        CenterCrop(size),
        ToTensor(),
        Normalize(mean, std),
    ]))

    loaded = load_dataset("imagefolder", data_dir=root)
    test_ds = loaded["test"]
    test_ds = test_ds.with_transform(test_transforms.apply_transforms)
    
    labels = test_ds.features["label"].names
    label2id, id2label = dict(), dict()
    for i, label in enumerate(labels):
        label2id[label] = str(i)
        id2label[str(i)] = label

    test_ds = test_ds.filter(lambda x: "_" not in id2label[str(x["label"])])

    model: MobileNetV2ForImageClassification = AutoModelForImageClassification.from_pretrained(
        pretrained_model_name_or_path,
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    ).eval().cuda()

    test_dl = DataLoader(test_ds, batch_size=64, pin_memory=True, num_workers=0)

    labels, preds = [], []
    with torch.inference_mode():
        for batch in tqdm(test_dl, desc="Processing batches..."):
            x = batch["pixel_values"].cuda()  # BxCxHxW
            y = batch["label"].cuda()  # B,
            output = model(x)
            logits = output.logits  # BxC
            yhat = torch.argmax(logits, dim=1)  # B,
            labels.append(y.cpu().numpy())
            preds.append(yhat.cpu().numpy())
           
    labels = np.concatenate(labels, axis=0)
    preds = np.concatenate(preds, axis=0)
    classes = np.unique(labels)
    names = [id2label[str(label)] for label in classes]
    cm = confusion_matrix(labels, preds, labels=classes)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=names)
    disp.plot(xticks_rotation="vertical")
    plt.show()
        