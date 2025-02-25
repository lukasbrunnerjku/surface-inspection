import bpy
import os.path as osp
from dataclasses import dataclass
from typing import Optional


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


def render_image(outfile: str):
    if osp.splitext(outfile)[1] == "png":
        bpy.context.scene.render.filepath = outfile
        bpy.ops.render.render(write_still=True)
        print(f"Rendered image saved at {outfile}")


if __name__ == "__main__":
    project_path = "C:/Users/lbrunn/projects/surface-inspection"
    folder = osp.join(project_path, "textures/wood/0047")
    outfile = osp.join(project_path, "image.png")

    material = bpy.data.materials["PBR_Material"]
    nodes = material.node_tree.nodes

    texture = Texture()
    texture.find_files(folder)
    texture.load_images(nodes)

    render_image(outfile)
