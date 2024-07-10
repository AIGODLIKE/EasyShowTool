import bpy
from enum import Enum
from typing import Final, Callable, ClassVar
from dataclasses import dataclass, field
from .utils import ColorTool
from mathutils import Color


class Colors(Enum):
    GREY: Final[str] = '#A1A1A1'  # float color
    ORANGE: Final[str] = '#ED9E5C'  # object color
    GREEN_GEO: Final[str] = '#00D6A3'  # geometry color
    GREEN_INT: Final[str] = '#598C5C'  # interface color
    BLUE: Final[str] = '#598AC3'  # string color
    PURPLE_VEC: Final[str] = '#6363C7'  # vector color
    PURPLE_IMG: Final[str] = '#633863'  # image color
    PINK_BOOL: Final[str] = '#CCA6D6'  # boolean color
    PINK_MAT: Final[str] = '#EB7582'  # material color


@dataclass
class ColorPaletteModel:
    name: ClassVar[str] = '.enn_palette'
    palette: ClassVar[bpy.types.Palette] = field(init=False)

    @classmethod
    def setup(cls):
        cls.palette = bpy.data.palettes.get(cls.name, bpy.data.palettes.new(cls.name))
        cls.palette.colors.clear()
        for color in Colors:
            c = cls.palette.colors.new()
            c.color = ColorTool.hex_2_rgb(color.value)
