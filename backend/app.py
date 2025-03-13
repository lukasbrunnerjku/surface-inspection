import base64
from flask import Flask, jsonify, request
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


@dataclass
class Item:
    pil_image: PngImageFile
    integer_label: int
    n_seen: int
    

def load_imagefolder(config: Config, fraction: float = 0.5):
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

    ds = ds.train_test_split(
        test_size=fraction,
        generator=np.random.default_rng(seed=42),
        shuffle=True,
        stratify_by_column="label",
    )["test"]  # Stratified; Keeps the same label distribution in each split.

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
dl = DataLoader(ds, batch_size=1, shuffle=True, collate_fn=collate_fn)

# Reset global state variables
n_seen = 0 
seen_items: list[Item] = []
loader = iter(dl)

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

@app.route('/api/reset', methods=['PUT'])
def do_reset():
    # Reset global state variables
    global n_seen, loader
    n_seen = 0 
    seen_items.clear()
    assert len(seen_items) == 0
    loader = iter(dl)
    return jsonify({"message": "Reset done successfully."})


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
        n_seen += 1

        seen_items.append(Item(
            pil_image=image,
            integer_label=integer_label,
            n_seen=n_seen
        ))
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


@app.route('/api/evaluation', methods=['POST'])
def get_eval():
    try:
        data = request.get_json()  # Get JSON data from frontend
        identifiers = data.get("draggedIdentifiers", [])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    identifiers = [int(i) for i in identifiers]
    identifiers = set(identifiers)

    if len(identifiers) > 0:
        pil_images, integer_labels = [], []
        for item in seen_items:
            if item.n_seen in identifiers:
                pil_images.append(item.pil_image)
                integer_labels.append(item.integer_label)

        preds = predict(pil_images, model, test_transforms)
        tgts = np.asarray(integer_labels)
        correct = (preds == tgts).sum()
        total = len(preds)
        acc = f"{100 * correct / total:.2f}"
        correct = f"{correct:d}"
        total = f"{total:d}"
    else:
        acc = "0.00"
        correct = "0"
        total = str(n_total)

    data = {
        "acc": acc,
        "correct": correct,
        "total": total,
    }
    return jsonify(data)


if __name__ == '__main__':
    """
    cd backend

    flask run

    The "flask run" will use the app.py code in the current directory.
    """
    app.run(debug=True)
