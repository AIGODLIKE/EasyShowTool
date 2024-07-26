from dataclasses import dataclass
from typing import ClassVar, Literal, Sequence

from mathutils import Vector
import bpy

PositionType = Literal[
    'top_left', 'top_right', 'bottom_left', 'bottom_right',
    'top_center', 'bottom_center', 'left_center', 'right_center'
]


class AreaPoint(Vector):
    """A point with a position and a type."""
    position_type: PositionType

    @classmethod
    def ui_scale(cls) -> float:
        return bpy.context.preferences.system.ui_scale

    def set_position_type(self, position_type: PositionType) -> 'AreaPoint':
        self.position_type = position_type
        return self

    def r2d_2_v2d(self) -> 'AreaPoint':
        """Convert the region 2d space to view 2d space."""
        return AreaPoint(bpy.context.region.view2d.region_to_view(*self.xy)) / self.ui_scale()

    def v2d_2_r2d(self) -> 'AreaPoint':
        """Convert the view 2d space to region 2d space."""
        return AreaPoint(bpy.context.region.view2d.view_to_region(*self.xy * self.ui_scale(), clip=False))

    def loc3d_2_v2d(self) -> 'AreaPoint':
        """Convert 3D space point to node editor 2d space."""
        return self / self.ui_scale()

    def v2d_2_loc3d(self) -> 'AreaPoint':
        """Convert 2D space point to 3D space."""
        return self * self.ui_scale()


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

    def get_oppo_area_point(self, point: AreaPoint) -> AreaPoint:
        match point.position_type:
            case 'top_left':
                return self.bottom_right
            case 'top_right':
                return self.bottom_left
            case 'bottom_left':
                return self.top_right
            case 'bottom_right':
                return self.top_left
            case 'top_center':
                return self.bottom_center
            case 'bottom_center':
                return self.top_center
            case 'left_center':
                return self.right_center
            case 'right_center':
                return self.left_center
            case _:
                raise ValueError(f"Invalid position type: {point.position_type}")

    def get_oppo_area_point_from_points(self, point: AreaPoint, points: Sequence[AreaPoint]) -> AreaPoint:
        """Get the opposite point of the point from the points list,e.g. top_left -> bottom_right
        :param point: the point to get the opposite point
        :param points: the points list, should be the corner points/ edge center points"""
        p_type: str = point.position_type
        if 'top' in p_type:
            p_type = p_type.replace('top', 'bottom')
        elif 'bottom' in p_type:
            p_type = p_type.replace('bottom', 'top')
        if 'left' in p_type:
            p_type = p_type.replace('left', 'right')
        elif 'right' in p_type:
            p_type = p_type.replace('right', 'left')

        for p in points:
            if p.position_type == p_type:
                return p

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
        return ((self.top_right + self.bottom_right) / 2).set_position_type('right_center')

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
