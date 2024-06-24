import bpy
from enum import Enum
from typing import Final, Callable, ClassVar
from dataclasses import dataclass, field
from .utils import ColorTool
from mathutils import Color


class Colors(Enum):
    WHITE: Final[Color] = [1.000168, 0.999956, 0.999928]
    ORANGE: Final[Color] = [0.846866, 0.341920, 0.107022]
    GREEN_GEO: Final[Color] = [0.000000, 0.672414, 0.366226]
    GREEN_INT: Final[Color] = [0.099899, 0.262251, 0.107023]
    BLUE: Final[Color] = [0.162028, 0.445194, 1.000024]
    PURPLE_VEC: Final[Color] = [0.124774, 0.124774, 0.571122]
    PURPLE_IMG: Final[Color] = [0.124774, 0.039546, 0.124774]
    GREY: Final[Color] = [0.356404, 0.356404, 0.356404]
    PINK_BOOL: Final[Color] = [0.603831, 0.381326, 0.672457]
    PINK_MAT: Final[Color] = [0.830770, 0.177888, 0.223228]


@dataclass
class ColorPaletteModel:
    name: ClassVar[str] = '.enn_palette'
    palette: ClassVar[bpy.types.Palette] = field(init=False)

    @classmethod
    def setup(cls):
        cls.palette = bpy.data.palettes.get(cls.name)
        if not cls.palette:
            cls.palette = bpy.data.palettes.new(cls.name)
            cls.palette.colors.clear()
            for color in Colors:
                c = cls.palette.colors.new()
                c.color = color[:3]
            # cls.palette.use_fake_user = True
