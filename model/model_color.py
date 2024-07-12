import enum

import bpy
from enum import Enum
from typing import Final, Callable, ClassVar
from dataclasses import dataclass, field
from .utils import ColorTool
from mathutils import Color
from pathlib import Path
from ..public_path import get_color_palettes_directory, get_color_palettes


class SocketColor(Enum):
    GREY: Final[str] = '#A1A1A1'  # float color
    ORANGE: Final[str] = '#ED9E5C'  # object color
    GREEN_GEO: Final[str] = '#00D6A3'  # geometry color
    GREEN_INT: Final[str] = '#598C5C'  # interface color
    BLUE: Final[str] = '#598AC3'  # string color
    PURPLE_VEC: Final[str] = '#6363C7'  # vector color
    PURPLE_IMG: Final[str] = '#633863'  # image color
    PINK_BOOL: Final[str] = '#CCA6D6'  # boolean color
    PINK_MAT: Final[str] = '#EB7582'  # material color


custom_colors = [
    '#ffffff',
    '#e5e5e5',
    '#a6a6a6',
    '#808080',
    '#383838',
    '#000000',
    '#ff5733',
    '#d4302f',
    '#d4302f',
    '#ffeb3c',
    '#ffc300',
    '#ff8d1a',
    '#a5d63f',
    '#44cf7c',
    '#00baad',
    '#2a82e4',
    '#7848ea',
]


@dataclass
class ColorPaletteModel:
    name: ClassVar[str] = '.est_palette'
    palette: ClassVar[bpy.types.Palette] = field(init=False)

    @classmethod
    def setup(cls):
        cls.palette = bpy.data.palettes.get(cls.name, bpy.data.palettes.new(cls.name))
        cls.palette.colors.clear()
        for color in SocketColor:
            c = cls.palette.colors.new()
            c.color = ColorTool.hex_2_rgb(color.value)

    def ensure_palette_images(self):
        path = get_color_palettes_directory()
        d = path.joinpath(SocketColor.__name__)
        custom_colors_dir = path.joinpath('custom')

        if not d.exists():
            d.mkdir()
        if not custom_colors_dir.exists():
            custom_colors_dir.mkdir()

        exists = get_color_palettes()

        for color in SocketColor:
            if color.name in exists[SocketColor.__name__]: continue
            full_name = color.value
            filepath = d.joinpath(full_name + '.jpg')
            if filepath.exists(): continue
            self.save_color_image(color.value, filepath)

        for color_str in custom_colors:
            if color_str in exists['custom']: continue
            full_name = color_str
            filepath = custom_colors_dir.joinpath(full_name + '.jpg')
            if filepath.exists(): continue
            self.save_color_image(color_str, filepath)

    def save_color_image(self, color: list[float, float, float], path: Path, size=16):
        c = ColorTool.set_alpha(ColorTool.hex_2_rgb(color), 1.0)
        pixels = list(c) * size * size
        image = bpy.data.images.new('tmp', width=size, height=size)
        image.pixels = pixels
        image.file_format = 'JPEG'
        image.filepath_raw = path.as_posix()
        image.save()
        bpy.data.images.remove(image)
