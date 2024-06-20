from mathutils import Vector
from typing import Sequence, Union, Final
import bpy
from dataclasses import dataclass


class VecTool:
    """Vec utility class. use to convert between view 2d , region 2d and 3d space."""

    @staticmethod
    def _size_2(v: float, r: bool = False) -> float:
        """
        convert grease pencil annotation location between 2d space to 3d space
        :param v: value
        :param r: reverse False: 3d -> 2d, True: 2d -> 3d
        :return: value
        """
        scale = bpy.context.preferences.system.ui_scale
        return v / scale if not r else v * scale

    @staticmethod
    def _vec_2(v: Vector, r: bool = False) -> Vector:
        """
        convert grease pencil annotation location between 2d space to 3d space
        :param v: value
        :param r: reverse False: 3d -> 2d, True: 2d -> 3d
        :return: value
        """
        scale = bpy.context.preferences.system.ui_scale
        return Vector((v[0] / scale, v[1] / scale, 1)) if not r else Vector((v[0] * scale, v[1] * scale, 1))

    @property
    def ui_scale(self) -> float:
        return bpy.context.preferences.system.ui_scale

    @staticmethod
    def r2d_2_v2d(location: Union[Vector, Sequence]) -> Vector:
        """Convert region 2d space point to node editor 2d view."""
        ui_scale = bpy.context.preferences.system.ui_scale
        x, y = bpy.context.region.view2d.region_to_view(location[0], location[1])
        return Vector((x / ui_scale, y / ui_scale))

    @staticmethod
    def v2d_2_r2d(location: Union[Vector, Sequence]) -> Vector:
        """Convert node editor 2d view point to region 2d space."""
        ui_scale = bpy.context.preferences.system.ui_scale
        x, y = bpy.context.region.view2d.view_to_region(location[0] * ui_scale, location[1] * ui_scale, clip=False)
        return Vector((x, y))

    @staticmethod
    def loc3d_2_v2d(location: Union[Vector, Sequence]) -> Vector:
        """Convert 3D space point to node editor 2d space."""
        return Vector((VecTool._size_2(location[0]), VecTool._size_2(location[1])))

    @staticmethod
    def v2d_2_loc3d(location: Union[Vector, Sequence]) -> Vector:
        """Convert 2D space point to 3D space."""
        return Vector((VecTool._size_2(location[0], r=True), VecTool._size_2(location[1], r=True)))

    @staticmethod
    def rotation_direction(v1: Union[Vector, Sequence], v2: Union[Vector, Sequence]) -> int:
        """Return the rotation direction of two vectors.
        CounterClockwise: 1
        Clockwise: -1
        """
        cross_z = v1[0] * v2[1] - v1[1] * v2[0]
        return 1 if cross_z >= 0 else -1


@dataclass(slots=True)
class ColorTool:
    """Grease Pencil Color utility class."""
    white: Final[str] = '#FFFFFF'  # white color
    orange: Final[str] = '#ED9E5C'  # object color
    green_geo: Final[str] = '#00D6A3'  # geometry color
    green_int: Final[str] = '#598C5C'  # interface color
    blue: Final[str] = '#598AC3'  # string color
    purple_vec: Final[str] = '#6363C7'  # vector color
    purple_img: Final[str] = '#633863'  # image color
    grey: Final[str] = '#A1A1A1'  # float color
    pink_bool: Final[str] = '#CCA6D6'  # boolean color
    pink_mat: Final[str] = '#EB7582'  # material color

    @staticmethod
    def hex_2_rgb(hex_color: str) -> list[float, float, float]:
        """Convert hex color to rgb color."""
        if hex_color.startswith('#'):
            hex = hex_color[1:]
        else:
            hex = hex_color
        return [int(hex[i:i + 2], 16) / 255 for i in (0, 2, 4)]
