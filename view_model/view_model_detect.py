from dataclasses import dataclass, field
from typing import Sequence, Optional, Literal, Callable

from mathutils import Vector

from ..model.model_gp_bbox import GPencilLayerBBox
from ..model.model_points import PointsArea
from ..model.utils import VecTool
from ..public_path import get_pref


@dataclass
class MouseDetectModel:
    """MouseDetectModel Model, a base class for detect mouse position with 2d grease pencil annotation.
    work in region 2d space.
    """

    bbox_model: 'GPencilLayerBBox' = Optional[None]

    d_edge: int = field(default_factory=lambda: get_pref().gp_performance.detect_edge_px)
    d_corner: int = field(default_factory=lambda: get_pref().gp_performance.detect_corner_px)
    d_rotate: int = field(default_factory=lambda: get_pref().gp_performance.detect_rotate_px)

    def bind_bbox(self, bbox_model: 'GPencilLayerBBox') -> 'MouseDetectModel':
        """Need to bind the bbox model to work."""
        self.bbox_model = bbox_model
        return self

    def detect_near(self, pos: Sequence | Vector) -> dict[str, tuple[Vector, int] | tuple[None, None]]:
        return {
            'corner': self._near_corners(pos, self.d_corner),
            'edge_center': self._near_edge_center(pos, self.d_edge),
            'corner_extrude': self._near_corners_extrude(pos, self.d_rotate + self.d_corner, self.d_rotate),
            'in_area': self.in_bbox_area(pos, self.d_edge)
        }

    def in_bbox_area(self, pos: Sequence | Vector, feather: int = 0) -> bool:
        """check if the pos is in the area defined by the points
        :param pos: the position to check, in r2d space
        :param feather: the feather to expand the area, unit: pixel
        :return: True if the pos is in the area, False otherwise
        """
        x, y = pos
        points = self.bbox_model.bbox_points_r2d
        top_left, top_right, bottom_left, bottom_right = points
        if not self.bbox_model.is_local:
            if feather != 0:
                top_left = (top_left[0] - feather, top_left[1] + feather)
                top_right = (top_right[0] + feather, top_right[1] + feather)
                bottom_left = (bottom_left[0] - feather, bottom_left[1] - feather)

            if top_left[0] < x < top_right[0] and bottom_left[1] < y < top_left[1]:
                return True
        else:
            polygon = [top_left, top_right, bottom_right, bottom_left]
            inside = False

            for i in range(4):
                p1, p2 = polygon[i], polygon[(i + 1) % 4]
                if (p1[1] > y) != (p2[1] > y) and (x < (p2[0] - p1[0]) * (y - p1[1]) / (p2[1] - p1[1]) + p1[0]):
                    inside = not inside
            return inside

    def bbox_in_area(self, points: list[Vector], all=True) -> bool:
        """check if the bbox is in the area defined by the points
        :param points: points that define the area, order: top_left, top_right, bottom_left, bottom_right
        :param all: if True, all the points need to be in the area, otherwise, any point in the area is ok
        """
        top_left, top_right, bottom_left, bottom_right = points
        bbox_points = self.bbox_model.bbox_points_r2d
        for p in bbox_points:
            if not (top_left[0] < p[0] < top_right[0] and bottom_left[1] < p[1] < top_left[1]):
                return False  # if not in the area
            if not all:
                return True
        return True

    def _near_edge_center(self, pos: Sequence | Vector, radius: int = 20) -> \
            tuple[Vector, int] | None:
        """check if the pos is near the edge center of the area defined by the points
        :param pos: the position to check
        :param radius: the radius of the edge center point
        :return: True if the pos is near the edge center, False otherwise
        """
        vec_pos = Vector((pos[0], pos[1]))
        points = self.bbox_model.edge_center_points_r2d
        for i, point in enumerate(points):
            vec_point = Vector(point)
            if (vec_pos - vec_point).length < radius:
                return vec_point, i
        return None, None

    def _near_corners(self, pos: Sequence | Vector, radius: int = 20) -> \
            tuple[Vector, int] | None:
        """check if the pos is near the corners of the area defined by the bounding box points
        :param pos: the position to check
        :param radius: the radius of the corner point
        :return: True if the pos is near the corners, False otherwise
        """
        vec_pos = Vector((pos[0], pos[1]))
        points = self.bbox_model.bbox_points_r2d
        for i, point in enumerate(points):
            vec_point = Vector(point)
            if (vec_pos - vec_point).length < radius:
                return vec_point, i
        return None, None

    def _near_corners_extrude(self, pos: Sequence | Vector, extrude: int = 15, radius: int = 15) -> \
            tuple[Vector, int] | None:

        """check if the pos is near the corner point extrude outward by 45 deg, space is default to r2d
        :param pos: the position to check
        :param extrude: the extrude distance
        :param radius: the radius of the extrude point
        :return: True if the pos is near the corners, False otherwise
        """
        vec = Vector(pos)
        points = self.bbox_model.corner_extrude_points_r2d(extrude)
        for i, point in enumerate(points):
            if (vec - point).length < radius:
                return point, i
        return None, None


@dataclass
class MouseState:
    mouse_pos: Vector = Vector((0, 0))
    mouse_pos_prev: Vector = Vector((0, 0))
    start_pos: Vector = Vector((0, 0))
    end_pos: Vector = Vector((0, 0))

    delta_vec_r2d: Vector = Vector((0, 0))
    delta_vec_v2d: Vector = Vector((0, 0))

    on_mouse_init: list[Callable] = field(default_factory=list)
    on_mouse_move: list[Callable] = field(default_factory=list)

    def init(self, event):
        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        self.start_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        self.end_pos = self.mouse_pos
        for callback in self.on_mouse_init:
            callback()

    def update_mouse_position(self, event):
        """Update the mouse position and the delta vector. Prepare for the handle_drag."""
        self.mouse_pos_prev = self.mouse_pos
        self.mouse_pos = Vector((event.mouse_region_x, event.mouse_region_y))
        self.end_pos = self.mouse_pos
        self.delta_vec_r2d = self.mouse_pos - self.mouse_pos_prev
        pre_v2d = VecTool.r2d_2_v2d(self.mouse_pos_prev)
        cur_v2d = VecTool.r2d_2_v2d(self.mouse_pos)
        self.delta_vec_v2d = cur_v2d - pre_v2d

        for callback in self.on_mouse_move:
            callback()

    def get_rotate_delta_angle(self, pivot_r2d: Vector) -> tuple[Literal[1, -1], float]:
        """Get the angle between the current mouse position and the previous mouse position.
        The angle is calculated based on the pivot point."""
        vec_1 = self.mouse_pos - pivot_r2d
        vec_2 = self.mouse_pos_prev - pivot_r2d
        # clockwise or counterclockwise
        inverse: Literal[1, -1] = VecTool.rotation_direction(vec_1, vec_2)
        angle = inverse * vec_1.angle(vec_2)
        return inverse, angle

    def drag_area(self) -> PointsArea:
        if self.start_pos.x > self.end_pos.x:
            # right to left
            left = self.end_pos.x
            right = self.start_pos.x
        else:
            left = self.start_pos.x
            right = self.end_pos.x
        if self.start_pos.y > self.end_pos.y:
            # bottom to top
            bottom = self.end_pos.y
            top = self.start_pos.y
        else:
            bottom = self.start_pos.y
            top = self.end_pos.y

        area = PointsArea(top=top, bottom=bottom, left=left, right=right)
        return area

    def is_move(self) -> bool:
        return self.start_pos.x > 0 and self.start_pos.y > 0
