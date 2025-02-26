from PIL import Image
import numpy as np
from pathlib import Path
from tqdm import tqdm


def tile(image: np.ndarray, patch_size: int) -> list[np.ndarray]:
    """Tile an image into smaller squares."""
    height, width, _ = image.shape

    assert height % patch_size == 0
    assert width % patch_size == 0

    patches = []
    for y in range(0, height, patch_size):
        for x in range(0, width, patch_size):
            patch = image[y:y+patch_size, x:x+patch_size]
            patches.append(patch)
    return patches


def read_image(image_path) -> np.ndarray:
    return np.array(Image.open(image_path))


def write_image(image_path, image: np.ndarray):
    image = Image.fromarray(image)
    image.save(image_path)


def build_imagefolder_dataset(outfolder: Path, infolder: Path, patch_size: int, train_fraction: float = 0.75):
    image_paths = sorted(infolder.glob("*.png"))
    for image_path in tqdm(image_paths, "Generating imagefolder dataset..."):
        image = read_image(image_path)
        patches = tile(image, patch_size)
        n_total = len(patches)

        train_folder = outfolder / "train" / image_path.stem
        train_folder.mkdir(parents=True, exist_ok=True)

        test_folder = outfolder / "test" / image_path.stem
        test_folder.mkdir(parents=True, exist_ok=True)

        n_train = int(n_total * train_fraction)
        for idx, image in enumerate(patches[:n_train]):
            write_image(train_folder / f"{idx:03d}.png", image)
        
        for idx, image in enumerate(patches[n_train:]):
            write_image(test_folder / f"{idx:03d}.png", image)


if __name__ == "__main__":
    infolder = r"C:\Users\lbrunn\projects\surface-inspection\images\wood"
    infolder = Path(infolder)
    assert infolder.exists()

    outfolder = r"C:\Users\lbrunn\projects\surface-inspection\datasets\wood"
    outfolder = Path(outfolder)
    outfolder.mkdir(parents=True, exist_ok=True)

    patch_size = 128

    build_imagefolder_dataset(outfolder, infolder, patch_size)
    