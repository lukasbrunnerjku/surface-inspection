"""
4k textures from https://www.texturecan.com

With this script the extracted texture folders are
preprocessed to follow the expected naming convention.

NOTE: Blender uses the OpenGL format for its normal maps.
"""
import re
from pathlib import Path
# from tqdm import tqdm
import shutil


def main(folder: Path):
    pattern: str = r"wood_\d{4}_4k_*"  # TODO
    texture_folders = []
    for texture_folder in folder.iterdir():
        m = re.search(pattern, str(texture_folder))
        if m is not None:
            x = m.group()  # ie. "wood_0044_4k_"
            new_name = x.split("_")[1]  # ie. "0044"
            new_texture_folder = folder / new_name
            texture_folder.rename(new_texture_folder)
            texture_folders.append(new_texture_folder)
    
    for texture_folder in texture_folders:
        for file in texture_folder.iterdir():
            name = file.name
            if "MACOS" in name:
                shutil.rmtree(file)  # Remove folder and its content.
            elif "color" in name:
                file.rename(file.with_stem("diffuse"))  # Keeps extentions as is.
            elif "height" in name:
                file.rename(file.with_stem("displacement"))  # Keeps extentions as is.
            elif "roughness" in name:
                file.rename(file.with_stem("roughness"))  # Keeps extentions as is.
            elif "normal_opengl" in name:
                file.rename(file.with_stem("normal"))  # Keeps extentions as is.
            else:
                file.unlink()  # Any other file is not needed and removed.
    

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    main(args.folder)
