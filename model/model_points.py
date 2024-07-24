from dataclasses import dataclass
from typing import ClassVar

from mathutils import Vector


@dataclass(slots=True)
class PointsArea:
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
