from dataclasses import dataclass
from typing import Any, Callable, Optional, Literal
import bpy
from math import degrees
from mathutils import Vector
from typing import ClassVar

from ..model.utils import Coord, EdgeCenter, VecTool
from ..model.model_gp_bbox import GreasePencilLayerBBox
from ..model.model_gp import BuildGreasePencilData


@dataclass
class ViewPan():
    padding: int = 30
    deltax: int = 0
    deltay: int = 0
    step: int = 10
    step_max = 30
    pan_count: int = 0

    def is_on_region_edge(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if the mouse is on the edge of the region."""
        self.deltax = self.deltax = 0
        width, height = bpy.context.area.width, bpy.context.area.height
        x, y = mouse_pos
        # speed up the pan
        if x < self.padding:
            self.deltax = -self.step
        elif x > width - self.padding:
            self.deltax = self.step

        if y < self.padding:
            self.deltay = -self.step
        elif y > height - self.padding:
            self.deltay = self.step

        if self.deltax or self.deltay:
            self.pan_count += 1
            return True

    def edge_pan(self) -> Vector:
        """only use in node editor window
        :return: the pan vector.
        """
        bpy.ops.view2d.pan(deltax=self.deltax, deltay=self.deltay)
        return Vector((self.deltax, self.deltay))


class TransformHandler:
    """Handle the transform operation in the modal."""
    bbox_model: GreasePencilLayerBBox = None
    build_model: BuildGreasePencilData = None
    on_start: Callable = None
    on_end: Callable = None

    def __init__(self, callback: Optional[Callable[..., Any]] = None):
        self.callback = callback

    def accept_event(self, event: bpy.types.Event) -> bool:
        ...  # subclass should implement this method

    def handle(self, event: bpy.types.Event, models: Optional[dict] = None, **kwargs) -> bool:
        # if key in self.__dict__: # set the attribute
        if self.bbox_model is None or self.build_model is None:
            if models:
                self.bbox_model = models.get('bbox_model', None)
                self.build_model = models.get('build_model', None)

        for key, value in kwargs.items():
            if key in self.__annotations__:
                setattr(self, key, value)
        if self.on_start:
            self.on_start(self)
        self.accept_event(event)
        if self.on_end is not None:
            self.on_end(self)


class MoveHandler(TransformHandler):
    delta_vec: Vector = None
    end_pos: tuple[int, int] = (0, 0)
    view_pan: ViewPan = None

    def __init__(self):
        super().__init__()
        self.view_pan = ViewPan()

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the move event in the modal."""
        if self.view_pan.is_on_region_edge((self.end_pos)):
            pan_vec = self.view_pan.edge_pan()
            self.build_model.move_active(pan_vec, space='v2d')
        elif not self.delta_vec:
            return False
        else:
            self.build_model.move_active(self.delta_vec, space='v2d')
        return True


class RotateHandler(TransformHandler):
    delta_degree: float = 0
    pivot: Vector = None
    mouse_pos: tuple[int, int] = (0, 0)
    mouse_pos_prev: tuple[int, int] = (0, 0)
    snap_degree: int = 0

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the rotate event in the modal."""
        pivot: Vector = self.bbox_model.center
        pivot_r2d: Vector = self.bbox_model.center_r2d
        vec_1 = Vector(self.mouse_pos) - pivot_r2d
        vec_2 = Vector(self.mouse_pos_prev) - pivot_r2d
        # clockwise or counterclockwise
        inverse: Literal[1, -1] = VecTool.rotation_direction(vec_1, vec_2)
        angle = inverse * vec_1.angle(vec_2)
        degree = degrees(angle)
        # snap
        if not event.shift:
            self.build_model.rotate_active(degree, pivot,space='v2d')
        else:
            self.delta_degree += abs(degree)
            if self.delta_degree > self.snap_degree:
                self.delta_degree = 0
                self.build_model.rotate_active(self.snap_degree * inverse, pivot,space='v2d')
        return True


class ScaleHandler(TransformHandler):
    # state
    vec_scale: Vector = None
    pivot: Vector = None
    # pass in
    delta_vec: Vector = None
    mouse_pos: tuple[int, int] = (0, 0)
    pos_near_edge_center: Vector = None
    pos_near_corner: Vector = None
    pt_edge_center: int = 0
    pt_corner: int = 0

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the scale event in the modal.
        :return: True if the scale is handled, False otherwise. Event will be accepted if True."""
        unify_scale = event.shift
        center_scale = event.ctrl
        if self.pos_near_edge_center:
            if center_scale:
                self.both_sides_edge_center(unify_scale)
            else:
                self.one_side_edge_center(unify_scale)
        elif self.pos_near_corner:
            if center_scale:
                self.both_sides_corner(unify_scale)
            else:
                self.one_side_corner(unify_scale)

        if not self.vec_scale: return False
        if not self.pivot: return False

        self.build_model.scale_active(self.vec_scale, self.pivot, space='v2d')
        return True

    def calc_both_side(self):
        pivot = self.bbox_model.center
        pivot_r2d = self.bbox_model.center_r2d
        size_x_v2d, size_y_v2d = self.bbox_model.size_v2d

        delta_x, delta_y = (self.delta_vec * 2).xy
        if self.mouse_pos[0] < pivot_r2d[0]:  # if on the left side
            delta_x = -delta_x
        if self.mouse_pos[1] < pivot_r2d[1]:  # if on the bottom side
            delta_y = -delta_y

        return pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y

    def calc_one_side(self):
        delta_x, delta_y = self.delta_vec.xy
        size_x_v2d, size_y_v2d = self.bbox_model.size_v2d

        return delta_x, delta_y, size_x_v2d, size_y_v2d

    def calc_scale(self, delta_x: float, delta_y: float, size_x_v2d: float, size_y_v2d: float) -> tuple[float, float]:
        scale_x = 1 + delta_x / size_x_v2d
        scale_y = 1 + delta_y / size_y_v2d
        return scale_x, scale_y

    def unify_scale(self, delta_x: float, delta_y: float, vec_scale: Vector) -> None:
        if abs(delta_x) > abs(delta_y):
            vec_scale.y = vec_scale.x
        else:
            vec_scale.x = vec_scale.y

    def both_sides_edge_center(self, unify_scale: bool):
        pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y = self.calc_both_side()
        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)

        if self.pos_near_edge_center[0] == pivot_r2d[0]:
            vec_scale = Vector((1, scale_y, 0))
        else:
            vec_scale = Vector((scale_x, 1, 0))

        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.vec_scale = vec_scale

    def both_sides_corner(self, unify_scale: bool):
        pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y = self.calc_both_side()
        if self.pos_near_corner[0] == self.bbox_model.min_x:
            delta_x = -delta_x
        if self.pos_near_corner[1] == self.bbox_model.min_y:
            delta_y = -delta_y

        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)
        vec_scale = Vector((scale_x, scale_y, 0))
        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.vec_scale = vec_scale

    def one_side_edge_center(self, unify_scale: bool):
        delta_x, delta_y, size_x_v2d, size_y_v2d = self.calc_one_side()
        points = self.bbox_model.edge_center_points_3d
        pivot_index = EdgeCenter.opposite(self.pt_edge_center)
        pivot: Vector = points[pivot_index]

        if EdgeCenter.point_on_left(self.pt_edge_center):
            delta_x = -delta_x
        if EdgeCenter.point_on_bottom(self.pt_edge_center):
            delta_y = -delta_y

        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)

        if EdgeCenter.point_on_left(self.pt_edge_center) or EdgeCenter.point_on_right(self.pt_edge_center):
            vec_scale = Vector((scale_x, 1, 0))
        else:
            vec_scale = Vector((1, scale_y, 0))

        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.vec_scale = vec_scale

    def one_side_corner(self, unify_scale: bool):
        delta_x, delta_y, size_x_v2d, size_y_v2d = self.calc_one_side()
        points = self.bbox_model.bbox_points_3d
        pivot_index = Coord.opposite(self.pt_corner)
        pivot = points[pivot_index]

        if Coord.point_on_left(self.pt_corner):
            delta_x = -delta_x
        if Coord.point_on_bottom(self.pt_corner):
            delta_y = -delta_y

        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)

        vec_scale = Vector((scale_x, scale_y, 0))
        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.vec_scale = vec_scale
