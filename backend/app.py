import base64
from flask import Flask, Response, jsonify
from flask_cors import CORS
import time
import json
from pathlib import Path
from torch.utils.data import DataLoader, Subset
from dataclasses import dataclass
from omegaconf import OmegaConf
from datasets import load_dataset
from io import BytesIO
from PIL.PngImagePlugin import PngImageFile


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
# import pdb; pdb.set_trace()

n_total = len(ds)
n_seen = 0 
dl = DataLoader(ds, batch_size=1, shuffle=True, collate_fn=collate_fn)
loader = iter(dl)


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
        
        label: str = id2label[str(item["label"])]

        n_seen += 1

    except StopIteration:
        image_base64 = ""
        label = ""
    
    data = {
        "label": label,  # "0044"
        "image_base64": image_base64,
        "n_seen": str(n_seen),
        "n_total": str(n_total),
    }
    return jsonify(data)


def process_task():
    for i in range(1, 2+1):
        time.sleep(1)  # Simulate work
        yield f"data: {json.dumps({'progress': i * 50})}\n\n"  # Send progress %


@app.route('/api/process', methods=['GET'])
def process():
    return Response(process_task(), mimetype='text/event-stream')  # Streaming response


if __name__ == '__main__':
    """
    cd backend

    flask run

    The "flask run" will use the app.py code in the current directory.
    """
    app.run(debug=True)
