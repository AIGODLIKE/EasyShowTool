from mathutils import Vector, Euler
from typing import Sequence, Union, ClassVar, Literal
import bpy
import numpy as np
from dataclasses import dataclass
from math import radians, degrees
from math import cos, sin, pow


class EulerTool:
    @staticmethod
    def to_rad(degree: Sequence, order: str = 'XYZ') -> Euler:
        return Euler((radians(d) for d in degree), order)

    @staticmethod
    def to_deg(radian: Sequence, order: str = 'XYZ') -> Euler:
        return Euler((degrees(d) for d in radian), order)

    @staticmethod
    def rotate_points(points: list[Vector], angle: float, pivot: Vector) -> list[Vector]:
        """Apply rotation to a list of points around a pivot."""
        rotated_points = [
            ((p - pivot) @ Euler((0, 0, angle), 'XYZ').to_matrix() + pivot).to_2d() for p in points
        ]
        return rotated_points


class ColorTool:
    """Grease Pencil Color utility class."""

    @staticmethod
    def hex_2_rgb(hex_color: str) -> list[float, float, float]:
        """Convert hex color to rgb color."""
        if hex_color.startswith('#'):
            hex = hex_color[1:]
        else:
            hex = hex_color
        return [int(hex[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    @staticmethod
    def set_alpha(color: list[float, float, float], alpha: float) -> list[float, float, float]:
        """Set the alpha value of the color."""
        return color + [alpha]

    @staticmethod
    def srgb_2_linear(c, gamma=2.4):
        if c < 0:
            return 0
        elif c < 0.04045:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** gamma

    @staticmethod
    def linear_2_srgb(c, gamma_value=2.4):
        if c < 0.0031308:
            srgb = 0.0 if c < 0.0 else c * 12.92
        else:
            srgb = 1.055 * pow(c, 1.0 / gamma_value) - 0.055

        return srgb


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
    def r2d_2_v2d(location: Vector | Sequence) -> Vector:
        """Convert region 2d space point to node editor 2d view."""
        ui_scale = bpy.context.preferences.system.ui_scale
        x, y = bpy.context.region.view2d.region_to_view(location[0], location[1])
        return Vector((x / ui_scale, y / ui_scale))

    @staticmethod
    def v2d_2_r2d(location: Vector | Sequence) -> Vector:
        """Convert node editor 2d view point to region 2d space."""
        ui_scale = bpy.context.preferences.system.ui_scale
        x, y = bpy.context.region.view2d.view_to_region(location[0] * ui_scale, location[1] * ui_scale, clip=False)
        return Vector((x, y))

    @staticmethod
    def loc3d_2_v2d(location: Vector | Sequence) -> Vector:
        """Convert 3D space point to node editor 2d space."""
        return Vector((VecTool._size_2(location[0]), VecTool._size_2(location[1])))

    @staticmethod
    def v2d_2_loc3d(location: Vector | Sequence) -> Vector:
        """Convert 2D space point to 3D space."""
        return Vector((VecTool._size_2(location[0], r=True), VecTool._size_2(location[1], r=True)))

    @staticmethod
    def rotation_direction(v1: Vector | Sequence, v2: Vector | Sequence) -> Literal[1, -1]:
        """Return the rotation direction of two vectors.
        CounterClockwise: 1
        Clockwise: -1
        """
        cross_z = v1[0] * v2[1] - v1[1] * v2[0]
        return 1 if cross_z >= 0 else -1

    @staticmethod
    def rotate_by_angle(v: Vector | Sequence, angle: float) -> Vector:
        """Rotate a vector by an angle."""
        c = cos(angle)
        s = sin(angle)
        return Vector((v[0] * c - v[1] * s, v[0] * s + v[1] * c))


@dataclass(slots=True)
class PointArea:
    """4 points to define an area."""
    top: int | float
    bottom: int | float
    left: int | float
    right: int | float

    indices: ClassVar = ((0, 1, 2), (2, 1, 3))  # for gpu batch drawing fan

    @property
    def top_left(self) -> Vector:
        return Vector((self.left, self.top))

    @property
    def top_right(self) -> Vector:
        return Vector((self.right, self.top))

    @property
    def bottom_left(self) -> Vector:
        return Vector((self.left, self.bottom))

    @property
    def bottom_right(self) -> Vector:
        return Vector((self.right, self.bottom))

    @property
    def top_center(self) -> Vector:
        return (self.top_left + self.top_right) / 2

    @property
    def bottom_center(self) -> Vector:
        return (self.bottom_left + self.bottom_right) / 2

    @property
    def left_center(self) -> Vector:
        return (self.top_left + self.bottom_left) / 2

    @property
    def right_center(self) -> Vector:
        return (self.top_right + self.bottom_right) / 2

    @property
    def order_points(self) -> list[Vector]:
        return [self.top_left, self.top_right, self.bottom_left, self.bottom_right]

    @property
    def line_order_points(self) -> list[Vector]:
        return [self.top_left, self.top_right, self.bottom_right, self.bottom_left]


class PointBase:
    """Base class for points in the node editor.
    Helps to determine the order and opposite point of a point."""
    order: ClassVar[dict[int, str]] = {}
    opp_order: ClassVar[dict[str, str]] = {}

    @classmethod
    def opposite(cls, point: int) -> int:
        p = cls.order[point]
        for k, v in cls.order.items():
            if v == cls.opp_order[p]:
                return k

    @classmethod
    def point_on_left(cls, point: int) -> bool:
        return 'left' in cls.order[point]

    @classmethod
    def point_on_bottom(cls, point: int) -> bool:
        return 'bottom' in cls.order[point]

    @classmethod
    def point_on_right(cls, point: int) -> bool:
        return 'right' in cls.order[point]

    @classmethod
    def point_on_top(cls, point: int) -> bool:
        return 'top' in cls.order[point]


@dataclass
class Coord(PointBase):
    order: ClassVar[dict[int, str]] = {
        0: 'top_left',
        1: 'top_right',
        2: 'bottom_left',
        3: 'bottom_right',

    }

    opp_order: ClassVar[dict[str, str]] = {
        'top_left': 'bottom_right',
        'top_right': 'bottom_left',
        'bottom_left': 'top_right',
        'bottom_right': 'top_left',
    }


@dataclass
class EdgeCenter(PointBase):
    order: ClassVar[dict[int, str]] = {
        0: 'top_center',
        1: 'bottom_center',
        2: 'left_center',
        3: 'right_center',
    }

    opp_order: ClassVar[dict[str, str]] = {
        'top_center': 'bottom_center',
        'bottom_center': 'top_center',
        'left_center': 'right_center',
        'right_center': 'left_center',
    }
