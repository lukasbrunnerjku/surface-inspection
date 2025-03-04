import base64
from flask import Flask, Response, jsonify
from flask_cors import CORS
import time
import json
from pathlib import Path
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
    print(ds)

    return ds, label2id, id2label


def pil_to_base64(image: PngImageFile) -> bytes:
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_image


config = OmegaConf.merge(
    OmegaConf.structured(Config()),
    OmegaConf.load("config.yaml"),
)
print(config)

ds, label2id, id2label = load_imagefolder(config)
ds.curr_idx = 0

app = Flask(__name__)
CORS(app)


@app.route('/api/data', methods=['GET'])
def get_data():
    """
    Open a browser and visit: http://localhost:5000/api/data to
    see the json response!
    """
    item = ds[ds.curr_idx]
    image: PngImageFile = item["image"]
    label: int = item["label"]
    
    try:
        encoded_image = pil_to_base64(image)
        ds.curr_idx += 1
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404

    data = {
        "text": "Hello from Flask Backend!",
        "image_base64": f"data:image/jpeg;base64,{encoded_image}",
        "index": str(ds.curr_idx),
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

    # import pdb; pdb.set_trace()
    # print("")
