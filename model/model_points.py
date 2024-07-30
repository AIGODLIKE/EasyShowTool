from dataclasses import dataclass
from typing import ClassVar, Literal, Sequence

from mathutils import Vector, Euler
import bpy

PositionType = Literal[
    'top_left', 'top_right', 'bottom_left', 'bottom_right',
    'top_center', 'bottom_center', 'left_center', 'right_center',
    'not_defined'
]


class AreaPoint(Vector):
    """A point with a position and a type."""
    _position_type: PositionType = 'not_defined'

    @property
    def position_type(self) -> PositionType:
        return self._position_type

    @classmethod
    def ui_scale(cls) -> float:
        return bpy.context.preferences.system.ui_scale

    def set_position_type(self, position_type: PositionType) -> 'AreaPoint':
        self._position_type = position_type
        return self

    def r2d_2_v2d(self) -> 'AreaPoint':
        """Convert the region 2d space to view 2d space."""
        return AreaPoint(bpy.context.region.view2d.region_to_view(*self.xy)) / self.ui_scale()

    def v2d_2_r2d(self) -> 'AreaPoint':
        """Convert the view 2d space to region 2d space."""
        return AreaPoint(
            bpy.context.region.view2d.view_to_region(*self.xy * self.ui_scale(), clip=False)).set_position_type(
            self.position_type)

    def loc3d_2_v2d(self) -> 'AreaPoint':
        """Convert 3D space point to node editor 2d space."""
        return self / self.ui_scale()

    def v2d_2_loc3d(self) -> 'AreaPoint':
        """Convert 2D space point to 3D space."""
        return self * self.ui_scale()

    def rotate_by_angle(self, angle: float, pivot: Vector) -> 'AreaPoint':
        """Rotate a vector by an angle."""
        pos_type = self.position_type
        new = ((self.to_3d() - pivot) @ Euler((0, 0, angle), 'XYZ').to_matrix() + pivot).to_2d()
        return AreaPoint(new).set_position_type(pos_type)

    # override the operators
    def __mul__(self, other) -> 'AreaPoint':
        """* operator"""
        return AreaPoint(super().__mul__(other)).set_position_type(self.position_type)

    def __truediv__(self, other) -> 'AreaPoint':
        """/ operator"""
        return AreaPoint(super().__truediv__(other)).set_position_type(self.position_type)

    def __add__(self, other) -> 'AreaPoint':
        """+ operator"""
        return AreaPoint(super().__add__(other)).set_position_type(self.position_type)

    def __sub__(self, other) -> 'AreaPoint':
        """- operator"""
        return AreaPoint(super().__sub__(other)).set_position_type(self.position_type)

    def __matmul__(self, other) -> 'AreaPoint':
        """@ operator"""
        return AreaPoint(super().__matmul__(other)).set_position_type(self.position_type)

    # Vector method override
    def to_2d(self) -> 'AreaPoint':
        return AreaPoint((super().to_2d())).set_position_type(self.position_type)

    def to_3d(self) -> 'AreaPoint':
        return AreaPoint((super().to_3d())).set_position_type(self.position_type)


@dataclass(slots=True)
class PointsArea:
    """4 points to define an area."""
    top: int | float = 0  # top y
    bottom: int | float = 0  # bottom y
    left: int | float = 0  # left x
    right: int | float = 0  # right x
    center: Vector = Vector((0, 0, 0))  # 3d

    indices: ClassVar = ((0, 1, 2), (2, 1, 3))  # for gpu batch drawing fan

    def setup(self, top: int | float, bottom: int | float, left: int | float, right: int | float):
        """Setup the area with top, bottom, left, right
        :param top: top y
        :param bottom: bottom y
        :param left: left x
        :param right: right x
        """
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    @property
    def size(self) -> Vector:
        return Vector((self.right - self.left, self.top - self.bottom))

    @property
    def top_left(self) -> AreaPoint:
        return AreaPoint((self.left, self.top)).set_position_type('top_left')

    @property
    def top_right(self) -> AreaPoint:
        return AreaPoint((self.right, self.top)).set_position_type('top_right')

    @property
    def bottom_left(self) -> AreaPoint:
        return AreaPoint((self.left, self.bottom)).set_position_type('bottom_left')

    @property
    def bottom_right(self) -> AreaPoint:
        return AreaPoint((self.right, self.bottom)).set_position_type('bottom_right')

    @property
    def top_center(self) -> AreaPoint:
        return ((self.top_left + self.top_right) / 2).set_position_type('top_center')

    @property
    def bottom_center(self) -> AreaPoint:
        return ((self.bottom_left + self.bottom_right) / 2).set_position_type('bottom_center')

    @property
    def left_center(self) -> AreaPoint:
        return ((self.top_left + self.bottom_left) / 2).set_position_type('left_center')

    @property
    def right_center(self) -> AreaPoint:
        res = ((self.top_right + self.bottom_right) / 2).set_position_type('right_center')
        return res

    @property
    def corner_points(self) -> tuple[AreaPoint, AreaPoint, AreaPoint, AreaPoint]:
        """Return the corner points in clockwise"""
        return self.top_left, self.top_right, self.bottom_left, self.bottom_right

    @property
    def corner_points_line_order(self) -> tuple[AreaPoint, AreaPoint, AreaPoint, AreaPoint]:
        """Return the corner points in line order, use for draw the bbox line"""
        return self.top_left, self.top_right, self.bottom_right, self.bottom_left

    @property
    def edge_center_points(self) -> tuple[AreaPoint, AreaPoint, AreaPoint, AreaPoint]:
        return self.top_center, self.right_center, self.bottom_center, self.left_center
