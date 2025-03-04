import sys
sys.path.append(".")

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from sklearn.metrics import ConfusionMatrixDisplay
from torchvision.utils import make_grid
import matplotlib.pyplot as plt
from tqdm import tqdm
from torchmetrics.image.fid import FrechetInceptionDistance
from torchvision.transforms import PILToTensor
import random

from classify.train import *


if __name__ == "__main__":
    root = r"C:\Users\lbrunn\projects\surface-inspection\datasets\wood"
    size = 128

    fid_transforms = Transforms(Compose([
        CenterCrop(size),
        PILToTensor(),  # FID requires: BxCxHxW; uint8
    ]))

    loaded = load_dataset("imagefolder", data_dir=root)
    train_ds = loaded["train"]
    train_ds = train_ds.with_transform(fid_transforms.apply_transforms)
    
    labels = train_ds.features["label"].names
    label2id, id2label = dict(), dict()
    for i, label in enumerate(labels):
        label2id[label] = str(i)
        id2label[str(i)] = label

    # TODO
    train_ds = train_ds.filter(lambda x: "_" not in id2label[str(x["label"])])

    train_dl = DataLoader(train_ds, batch_size=128, pin_memory=False, num_workers=0)

    images, labels = [], []
    for batch in tqdm(train_dl, desc="Processing batches..."):
        x = batch["pixel_values"]  # BxCxHxW
        images.append(x)
        y = batch["label"]  # B,
        labels.append(y)

    images = torch.concat(images, dim=0)
    labels = torch.concat(labels, dim=0)
    classes = torch.unique(labels)
    names = [id2label[str(label.item())] for label in classes]
    N = len(classes)

    fid = FrechetInceptionDistance().cuda()
    fid.set_dtype(torch.float32)
    fid.inception.INPUT_IMAGE_SIZE = size

    name = "0044"
    i = names.index(name)
    topk = 10

    fid_scores = []
    fid.reset_real_features = False
    imgs = images[labels == classes[i]].cuda()  # BxCxHxW; uint8
    fid.update(imgs=imgs, real=True)

    for j in range(N):
        if i == j:  # Skip.
            continue

        imgs = images[labels == classes[j]].cuda()
        fid.update(imgs=imgs, real=False)
        fid_score = fid.compute().cpu().numpy()
        fid.reset()
        fid_scores.append(fid_score)
    
    fid_scores = np.stack(fid_scores)
    indices = np.argsort(fid_scores)  # Ascending order.
    ids = np.array([j for j in range(N)])[indices[:topk]]
    topk_names = [id2label[str(classes[i].item())] for i in ids]

    print("Real:", id2label[str(classes[i].item())])
    print("Fakes:", topk_names)

    # TODO
    idx = ids[0]  # Most similar.
    reals = images[labels == classes[i]]  # BxCxHxW; uint8
    fakes = images[labels == classes[idx]]  # BxCxHxW; uint8

    real_indices = torch.randperm(len(reals))
    n_reals = len(reals)
    fake_indices = torch.randperm(len(fakes))
    n_fakes = len(fakes)

    fig1, ax1 = plt.subplots()
    grid1 = make_grid([reals[real_indices[0]], fakes[fake_indices[0]]], nrow=2)
    grid1 = grid1.permute(1, 2, 0).numpy()  # HxWxC
    plt.imshow(grid1)

    fig2, ax2 = plt.subplots()
    n_row = 4
    n_total = n_row * n_row
    selection = []
    for n in range(n_total):
        if random.random() > 0.5:
            img = reals[random.randint(1, n_reals - 1)]
        else:
            img = fakes[random.randint(1, n_fakes - 1)]
        selection.append(img)
    grid2 = make_grid(selection, nrow=n_row)
    grid2 = grid2.permute(1, 2, 0).numpy()  # HxWxC
    plt.imshow(grid2)

    plt.show()

    # cm = np.zeros((N, N), dtype=np.float32) 
    # for i in tqdm(range(N), desc="Building FID-based confusion matrix..."):
    #     fid.reset_real_features = True
    #     fid.reset()
    #     fid.reset_real_features = False

    #     imgs = images[labels == classes[i]].cuda()  # BxCxHxW; uint8
    #     fid.update(imgs=imgs, real=True)
        
    #     for j in range(N):
    #         if i == j:  # Skip.
    #             continue

    #         if cm[j, i] > 0.0:  # Symmetric.
    #             cm[i, j] = cm[j, i]
    #             continue

    #         imgs = images[labels == classes[j]].cuda()
    #         fid.update(imgs=imgs, real=False)
    #         fid_score = fid.compute().cpu().numpy()
    #         cm[i, j] = fid_score
    #         fid.reset()

    # disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=names)
    # disp.plot(xticks_rotation="vertical")
    # plt.show()

    # confusion matrix is super overcrowded, values should be in 0 to 1 range for 
    # better visualization, 2 decimals (softmax and round)
