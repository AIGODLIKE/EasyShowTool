from dataclasses import dataclass
from typing import ClassVar

from mathutils import Vector


@dataclass(slots=True)
class PointsArea:
    """4 points to define an area."""
    top: int | float = 0 # top y
    bottom: int | float = 0 # bottom y
    left: int | float = 0 # left x
    right: int | float = 0 # right x
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
    def corner_points(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the corner points in clockwise"""
        return self.top_left, self.top_right, self.bottom_left, self.bottom_right

    @property
    def corner_points_line_order(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the corner points in line order, use for draw the bbox line"""
        return self.top_left, self.top_right, self.bottom_right, self.bottom_left

    @property
    def edge_center_points(self) -> tuple[Vector, Vector, Vector, Vector]:
        return self.top_center, self.right_center, self.bottom_center, self.left_center

    @property
    def corner_points_dict(self) -> dict[str, Vector]:
        """Return the corner points as a dictionary, use for calc the opposite corner"""
        return {'top_left': self.top_left, 'top_right': self.top_right,
                'bottom_left': self.bottom_left, 'bottom_right': self.bottom_right}

    @property
    def edge_center_points_dict(self) -> dict[str, Vector]:
        """Return the edge center points as a dictionary, use for calc the opposite edge center"""
        return {'top_center': self.top_center, 'right_center': self.right_center,
                'bottom_center': self.bottom_center, 'left_center': self.left_center}
