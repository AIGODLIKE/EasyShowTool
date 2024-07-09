from mathutils import Vector, Euler
from typing import Sequence, Union, Final, ClassVar
import bpy
from dataclasses import dataclass
from enum import Enum
from math import radians, degrees


class EulerTool:
    @staticmethod
    def to_rad(degree: Sequence) -> Euler:
        return Euler((radians(d) for d in degree), 'XYZ')

    @staticmethod
    def to_deg(radian: Sequence) -> Euler:
        return Euler((degrees(d) for d in radian), 'XYZ')


class ShootAngles(Enum):
    """Euler angles for the shooting.
    shoot will be on top(xy plane, z up), so the enum members are the angles to rotate the object to face the camera."""
    TOP_LEFT_FRONT: Euler = Euler(EulerTool.to_rad((-67.8044, -32.8686, -13.4876)), 'XYZ')
    TOP_LEFT_FRONT_45: Euler = Euler(EulerTool.to_rad((-35.2644, -30, -35.2644)), 'XYZ')

    TOP: Euler = Euler(EulerTool.to_rad((0, 0, 0)), 'XYZ')
    FRONT: Euler = Euler(EulerTool.to_rad((-90, 0, 0)), 'XYZ')
    LEFT: Euler = Euler(EulerTool.to_rad((0, -90, -90)), 'XYZ')
    RIGHT: Euler = Euler(EulerTool.to_rad((0, 90, 90)), 'XYZ')
    BOTTOM: Euler = Euler(EulerTool.to_rad((0, 180, 0)), 'XYZ')


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
