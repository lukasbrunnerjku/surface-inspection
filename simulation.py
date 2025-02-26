import bpy
import os.path as osp
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

r"""
How to install new packages.

1. Open the terminal
    cd "C:\Program Files\Blender Foundation\Blender 4.2\4.2\python\bin"

2. pip install package_name
    python.exe -m pip install tqdm

Details on installation:
    python.exe -m pip show tqdm

Location:
    C:\Users\lbrunn\AppData\Roaming\Python\Python311\site-packages
"""

import sys
sys.path.append(r"C:\Users\lbrunn\AppData\Roaming\Python\Python311\site-packages")
from tqdm import tqdm

@dataclass
class Texture:
    diffuse: Optional[str] = None
    normal: Optional[str] = None
    roughness: Optional[str] = None
    displacement: Optional[str] = None

    def find_files(self, folder: str):
        for filename in ["diffuse", "normal", "roughness", "displacement"]:
            for ext in ["png", "jpg"]:
                filepath = osp.join(folder, f"{filename}.{ext}")
                if osp.exists(filepath):
                    setattr(self, filename, filepath)
                    break
            else:
                print(f"Warning: {filename} not found in {folder}")

    def load_images(self, nodes):
        for node in nodes:
            if node.label == "diffuse":
                if self.diffuse is not None:
                    image = bpy.data.images.load(self.diffuse)
                    node.image = image
                    print(f"Loaded {self.diffuse} image into node.")
            elif node.label == "normal":
                if self.normal is not None:
                    image = bpy.data.images.load(self.normal)
                    node.image = image
                    print(f"Loaded {self.normal} image into node.")
            elif node.label == "roughness":
                if self.roughness is not None:
                    image = bpy.data.images.load(self.roughness)
                    node.image = image
                    print(f"Loaded {self.roughness} image into node.")
            elif node.label == "displacement":
                if self.displacement is not None:
                    image = bpy.data.images.load(self.displacement)
                    node.image = image
                    print(f"Loaded {self.displacement} image into node.")

    def set_mixer_factor(self, nodes, factor: float):
        for node in nodes:
            if node.label == "mixer":
                node.inputs[0].default_value = factor
                break
        else:
            print("Could not set mixer factor.")

    def set_rgb_color(self, nodes, rgb: list[float]):
        for node in nodes:
            if node.label == "color":
                node.inputs[4].default_value[0] = rgb[0]
                node.inputs[4].default_value[1] = rgb[1]
                node.inputs[4].default_value[2] = rgb[2]
                break
        else:
            print("Could not set rgb color.")


def render_to(outfile: str):
    p, ext = osp.splitext(outfile)
    if ext != ".png":
        outfile = p + ".png"
    
    bpy.context.scene.render.filepath = outfile
    bpy.ops.render.render(write_still=True)
    print(f"Rendered image saved at {outfile}")


@dataclass
class Color:
    name: str
    rgb: list[float]


def build_images(infolder: Path, outfolder: Path, colors: list[Color]):
    material = bpy.data.materials["PBR_Material"]
    nodes = material.node_tree.nodes
    ext = ".png"

    subfolders = sorted(infolder.iterdir())

    n_total = len(subfolders) * (len(colors) + 1)
    pbar = tqdm(desc="Generating images...", total=n_total)

    for subfolder in subfolders:  # ie. "textures/wood/0004"
        texture = Texture()
        texture.find_files(subfolder)
        texture.load_images(nodes)
        texture.set_mixer_factor(nodes, 0.0)  # Keep original color.

        # Render and save in original color.
        filename = f"{subfolder.name}{ext}"  # ie. "0004.png"
        outfile = str(outfolder / filename)
        render_to(outfile)
        pbar.update(1)

        # Render and save colorized versions.
        texture.set_mixer_factor(nodes, 0.5)  # Mix with original color.
        for color in colors:
            texture.set_rgb_color(nodes, color.rgb)
            filename = f"{subfolder.name}_{color.name}{ext}"   # ie. "0004_red.png"
            outfile = str(outfolder / filename)
            render_to(outfile)
            pbar.update(1)
        
    pbar.close()


if __name__ == "__main__":
    COLORS = [
        Color("red", [1, 0, 0]),
        Color("green", [0, 1, 0]),
        Color("blue", [0, 0, 1]),
        Color("yellow", [1, 1, 0]),
        Color("purple", [1, 0, 1]),
        Color("orange", [1, 0.5, 0]),
        Color("pink", [1, 0.5, 0.5]),
    ]

    infolder = Path("C:/Users/lbrunn/projects/surface-inspection/textures/wood")
    outfolder = Path("C:/Users/lbrunn/projects/surface-inspection/images/wood")
    build_images(infolder, outfolder, COLORS)
    
    # project_path = "C:/Users/lbrunn/projects/surface-inspection"
    # folder = osp.join(project_path, "textures/wood/0047")
    # outfile = osp.join(project_path, "image.png")

    # material = bpy.data.materials["PBR_Material"]
    # nodes = material.node_tree.nodes

    # texture = Texture()
    # texture.find_files(folder)
    # texture.load_images(nodes)
    # texture.set_mixer_factor(nodes, 0.5)
    # texture.set_rgb_color(nodes, [1.0, 0.0, 0.0])

    # render_to(outfile)
