import bpy
from typing import ClassVar
from dataclasses import dataclass, field

from .data_enums import SocketColor, custom_colors
from .utils import ColorTool
from pathlib import Path
from ..public_path import get_color_palettes_directory


@dataclass
class ColorPaletteModel:
    name: ClassVar[str] = '.est_palette'
    palette: ClassVar[bpy.types.Palette] = field(init=False)

    paths: ClassVar[list[Path]] = []
    pv_coll: ClassVar[dict] = {}
    icon_id: ClassVar[dict[str, int]] = {}

    @classmethod
    def ensure_palette_images(cls, create: bool = False):
        path = get_color_palettes_directory()
        d = path.joinpath(SocketColor.__name__)
        custom_colors_dir = path.joinpath('Preset')

        if not d.exists():
            d.mkdir()
        if not custom_colors_dir.exists():
            custom_colors_dir.mkdir()

        cls.paths = []

        for color in SocketColor:
            full_name = color.value
            filepath = d.joinpath(full_name + '.jpg')
            if not filepath.exists() and create:
                cls.save_color_image(color.value, filepath)
            cls.paths.append(filepath)

        for color_str in custom_colors:
            full_name = color_str
            filepath = custom_colors_dir.joinpath(full_name + '.jpg')
            if not filepath.exists() and create:
                cls.save_color_image(color_str, filepath)
            cls.paths.append(filepath)

    @staticmethod
    def save_color_image(color: list[float, float, float], path: Path, size=16):
        c = ColorTool.set_alpha(ColorTool.hex_2_rgb(color), 1.0)
        pixels = list(c) * size * size
        image = bpy.data.images.new('tmp', width=size, height=size)
        image.pixels = pixels
        image.file_format = 'JPEG'
        image.filepath_raw = path.as_posix()
        image.save()
        bpy.data.images.remove(image)

    @classmethod
    def get_color_icon_id(cls, color: str) -> int:
        icon_id = cls.icon_id.get(color)
        return icon_id if icon_id else cls.icon_id.get(SocketColor.GREY.value)

    @classmethod
    def register_color_icon(cls):
        if bpy.app.background: return

        cls.ensure_palette_images()

        from bpy.utils import previews
        pcoll = previews.new()
        for icon_path in cls.paths:
            if icon_path.stem in pcoll:
                continue
            pcoll.load(icon_path.stem, icon_path.as_posix(), 'IMAGE')
            cls.icon_id[icon_path.stem] = pcoll.get(icon_path.stem).icon_id
        cls.pv_coll['est_palette_pv'] = pcoll

        # print('PATHS!!!!!!!!!!!!', cls.paths)
        # print("ICON!!!!!!!!!!!!", cls.icon_id)

    @classmethod
    def unregister_color_icon(cls):
        if bpy.app.background: return

        from bpy.utils import previews
        for pcoll in cls.pv_coll.values():
            previews.remove(pcoll)
        cls.pv_coll.clear()
