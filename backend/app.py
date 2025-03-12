import base64
from flask import Flask, jsonify
from flask_cors import CORS
from torch.utils.data import DataLoader, Subset
from dataclasses import dataclass
from omegaconf import OmegaConf
from datasets import load_dataset
from io import BytesIO
from PIL.PngImagePlugin import PngImageFile
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend!

import matplotlib.pyplot as plt
import io
import numpy as np
import torch
from torchvision.transforms import (
    CenterCrop,
    Compose,
    Normalize,
    ToTensor,
)
from transformers import AutoModelForImageClassification
from transformers.models.mobilenet_v2 import MobileNetV2ForImageClassification
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay


@dataclass
class Config:
    dataset_path: str = ""
    dataset_split: str = "test"
    labels: tuple[str] = ("", "")
    pretrained_model_name_or_path: str = ""
    image_size: int = 128
    image_mean: float = 0.5
    image_std: float = 0.5
    

def load_imagefolder(config: Config):
    ds = load_dataset(
        "imagefolder",
        data_dir=config.dataset_path,
        split=config.dataset_split,
    )

    labels = ds.features["label"].names
    label2id, id2label = dict(), dict()
    for i, label in enumerate(labels):
        label2id[label] = str(i)
        id2label[str(i)] = label

    ds = ds.filter(lambda x: id2label[str(x["label"])] in config.labels)

    return ds, label2id, id2label


def pil_to_base64(image: PngImageFile) -> bytes:
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_image


def collate_fn(batch):
    return batch  # [{"image": ..., "label": ...}, {...}, ...]


@torch.inference_mode()
def predict(
    images: list[PngImageFile],
    model: MobileNetV2ForImageClassification,
    transforms: Compose,
) -> np.ndarray:
    """Transform images for classification model and predict integer lables."""
    transformed_images = []
    for img in images:
        transformed_images.append(transforms(img.convert("RGB")))  # CxHxW
    transformed_images = torch.stack(transformed_images, dim=0).cuda()  # BxCxHxW
    
    predictions = torch.argmax(model(transformed_images).logits, dim=1).cpu().numpy()  # B,
    return predictions


def get_confusion_matrix_base64(tgts: np.ndarray, preds: np.ndarray):
    classes = np.unique(np.concatenate([tgts, preds], axis=0))
    names = [id2label[str(label)] for label in classes]
    cm = confusion_matrix(tgts, preds, labels=classes)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=names)
    disp.plot(xticks_rotation="vertical")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    encoded_image = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    image_base64 = f"data:image/jpeg;base64,{encoded_image}"
    return image_base64


config = OmegaConf.merge(
    OmegaConf.structured(Config()),
    OmegaConf.load("config.yaml"),
)

ds, label2id, id2label = load_imagefolder(config)

examples = []
labels: list[int] = ds["label"]
indices = list(range(len(ds)))
for label in config.labels:
    i = labels.index(int(label2id[label]))
    indices.pop(i)

    image = ds[i]["image"]
    encoded_image = pil_to_base64(image)
    image_base64 = f"data:image/jpeg;base64,{encoded_image}"
    
    examples.append({"image_base64": image_base64, "label": label})

ds = Subset(ds, indices)  # Remove examples from dataset.

n_total = len(ds)
n_seen = 0 
dl = DataLoader(ds, batch_size=1, shuffle=True, collate_fn=collate_fn)
loader = iter(dl)

seen_pil_images, seen_integer_labels = [], []

test_transforms = Compose([
    CenterCrop(config.image_size),
    ToTensor(),
    Normalize(config.image_mean, config.image_std),
])

model: MobileNetV2ForImageClassification = AutoModelForImageClassification.from_pretrained(
    config.pretrained_model_name_or_path,
).eval().cuda()

app = Flask(__name__)
CORS(app)


@app.route('/api/examples', methods=['GET'])
def get_examples():
    """
    Open a browser to see the json response, visit:
    http://localhost:5000/api/examples
    """
    return jsonify(examples)


@app.route('/api/next_item', methods=['GET'])
def get_next():
    """
    Open a browser to see the json response, visit:
    http://localhost:5000/api/next_item
    """
    global n_seen

    try:
        batch = next(loader)
        item = batch[0]

        image: PngImageFile = item["image"]
        encoded_image = pil_to_base64(image)
        image_base64 = f"data:image/jpeg;base64,{encoded_image}"
        
        integer_label = item["label"]
        label: str = id2label[str(integer_label)]

        seen_pil_images.append(image)
        seen_integer_labels.append(integer_label)

        n_seen += 1

    except StopIteration:
        image_base64 = ""
        label = ""
    
    data = {
        "label": label,  # ie. "0044"
        "image_base64": image_base64,
        "n_seen": str(n_seen),
        "n_total": str(n_total),
    }
    return jsonify(data)


@app.route('/api/evaluation', methods=['GET'])
def get_eval():
    if len(seen_pil_images) > 0:
        preds = predict(seen_pil_images, model, test_transforms)
        tgts = np.asarray(seen_integer_labels)
        correct = (preds == tgts).sum()
        total = len(preds)
        acc = f"{100 * correct / total:.2f}"
        correct = f"{correct:d}"
        total = f"{total:d}"
        # image_base64 = get_confusion_matrix_base64(tgts, preds)
    else:
        acc = correct = total = ""
        # image_base64 = ""

    data = {
        "acc": acc,
        "correct": correct,
        "total": total,
        # "image_base64": image_base64,
    }
    return jsonify(data)


if __name__ == '__main__':
    """
    cd backend

    flask run

    The "flask run" will use the app.py code in the current directory.
    """
    app.run(debug=True)
