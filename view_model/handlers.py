from dataclasses import dataclass
from typing import Any, Callable, Optional, Literal
import bpy
from math import degrees
from mathutils import Vector
from typing import ClassVar

from ..model.utils import Coord, EdgeCenter, VecTool
from ..model.model_gp_bbox import GPencilLayerBBox
from ..model.model_gp import BuildGreasePencilData


@dataclass
class ViewPan:
    """Handle the pan operation in the modal. only use in node editor window"""
    padding: int = 30
    deltax: int = 0
    deltay: int = 0
    step: int = 10
    step_max: int = 50  # max step
    pan_count: int = 0  # count the pan event, higher the count, faster the pan

    pan_pos: tuple[int, int] = (0, 0)
    pan_post_prev: tuple[int, int] = (0, 0)

    def is_on_region_edge(self, mouse_pos: tuple[int, int]) -> bool:
        """Check if the mouse is on the edge of the region."""
        width, height = bpy.context.area.width, bpy.context.area.height
        for region in bpy.context.area.regions:
            if region.type == 'WINDOW':
                continue
            elif region.type == 'UI':
                width -= region.width
            elif region.type == 'HEADER':
                height -= region.height

        x, y = mouse_pos
        self.deltax = self.deltay = 0
        # speed up the pan
        if x < self.padding:
            self.deltax = -self.step
        elif x > width - self.padding:
            self.deltax = self.step

        if y < self.padding:
            self.deltay = -self.step
        elif y > height - self.padding:
            self.deltay = self.step

        if self.deltay or self.deltax:
            self.pan_count += 1
            if self.pan_count < self.step_max:
                self.step += 1
            return True

    def edge_pan(self, event) -> Vector:
        """pan view return: the pan vector."""
        self.pan_post_prev: Vector = VecTool.r2d_2_v2d((event.mouse_region_x, event.mouse_region_y))
        bpy.ops.view2d.pan(deltax=self.deltax, deltay=self.deltay)
        self.pan_pos: Vector = VecTool.r2d_2_v2d((event.mouse_region_x, event.mouse_region_y))
        return self.pan_pos - self.pan_post_prev


@dataclass
class TransformHandler:
    """Handle the complex transform operation in the modal.
    state attr can be pass in the callback function to update the view."""
    bbox_model: GPencilLayerBBox = None  # init by drag modal
    build_model: BuildGreasePencilData = None  # init by drag modal
    # callback
    call_before: Optional[Callable] = None
    call_after: Optional[Callable] = None

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
        if self.call_before:
            self.call_before(self)
        self.accept_event(event)
        if self.call_after is not None:
            self.call_after(self)


@dataclass
class MoveHandler(TransformHandler):
    # state
    total_move: Vector = Vector((0, 0))  # value between the last mouse move and the first mouse move
    delta_move: Vector = None  # compare to the last mouse move
    # in
    delta_vec_v2d: Vector = None
    end_pos: tuple[int, int] = (0, 0)

    view_pan: ViewPan = None

    def __post_init__(self):
        self.view_pan = ViewPan()

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the move event in the modal."""
        if not self.delta_vec_v2d:
            return False
        self.build_model.move_active(self.delta_vec_v2d, space='v2d')
        self.delta_move = self.delta_vec_v2d
        self.total_move += self.delta_vec_v2d
        if self.view_pan.is_on_region_edge(self.end_pos):
            pan_vec = self.view_pan.edge_pan(event)
            self.build_model.move_active(pan_vec, space='v2d')
            self.total_move += pan_vec
        return True


@dataclass
class RotateHandler(TransformHandler):
    # state
    total_degree: float = 0
    delta_degree: float = 0
    # in
    pivot: Vector = None
    mouse_pos: tuple[int, int] = (0, 0)
    mouse_pos_prev: tuple[int, int] = (0, 0)
    snap_degree: int = 0
    snap_degree_count: int = 0

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the rotate event in the modal."""
        if not self.pivot:
            self.pivot = self.bbox_model.center_v2d
            self.pivot_r2d = self.bbox_model.center_r2d

        vec_1 = Vector(self.mouse_pos) - self.pivot_r2d
        vec_2 = Vector(self.mouse_pos_prev) - self.pivot_r2d
        # clockwise or counterclockwise
        inverse: Literal[1, -1] = VecTool.rotation_direction(vec_1, vec_2)
        angle = inverse * vec_1.angle(vec_2)
        degree = degrees(angle)

        # snap
        if not event.shift:
            self.delta_degree += degree
            self.build_model.rotate_active(degree, self.pivot , space='v2d')
            self.total_degree += degree
        else:
            self.snap_degree_count += abs(degree)
            if self.snap_degree_count > self.snap_degree:
                self.snap_degree_count = 0
                self.delta_degree += self.snap_degree * inverse
                self.build_model.rotate_active(self.snap_degree * inverse, self.pivot , space='v2d')
                self.total_degree += self.snap_degree * inverse
        return True


# TODO need to use ScalePivot class to refactor the scale handler

# @dataclass
# class ScalePivot():
#     # in
#     bbox_model: GPencilLayerBBox
#     pivot_type: Literal['edge_center', 'corner', 'center']
#     pt_edge_center: int = 0
#     pt_corner: int = 0
#     # out
#     position: Vector = None
#
#     def __post_init__(self):
#         self.set_pivot()
#
#     def set_pivot(self):
#         if self.pivot_type == 'edge_center':
#             self.position = self.edge_center()
#         elif self.pivot_type == 'corner':
#             self.position = self.corner()
#         elif self.pivot_type == 'center':
#             self.position = self.center()
#
#     def edge_center(self) -> tuple[Vector, Vector]:
#         points = self.bbox_model.edge_center_points_3d
#         pivot_index = EdgeCenter.opposite(self.pt_edge_center)
#         pivot: Vector = points[pivot_index]
#         return pivot
#
#     def corner(self) -> tuple[Vector, Vector]:
#         points = self.bbox_model.bbox_points_3d
#         pivot_index = Coord.opposite(self.pt_corner)
#         pivot = points[pivot_index]
#         return pivot
#
#     def center(self) -> Vector:
#         return self.bbox_model.center


@dataclass
class ScaleHandler(TransformHandler):
    # state
    total_scale: Vector = Vector((1, 1, 1))
    delta_scale: Vector = None
    pivot: Vector = None
    pivot_local: Vector = None
    degree_local: float = 0
    # pass in
    delta_vec_v2d: Vector = None
    mouse_pos: tuple[int, int] = (0, 0)
    pos_edge_center: Vector = None
    pos_corner: Vector = None
    pt_edge_center: int = 0
    pt_corner: int = 0

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the scale event in the modal.
        :return: True if the scale is handled, False otherwise. Event will be accepted if True."""
        unify_scale = event.shift
        center_scale = event.ctrl

        if self.pos_edge_center:
            if center_scale:
                self.both_sides_edge_center(unify_scale)
            else:
                self.one_side_edge_center(unify_scale)
        elif self.pos_corner:
            if center_scale:
                self.both_sides_corner(unify_scale)
            else:
                self.one_side_corner(unify_scale)

        if not self.delta_scale: return False
        if not self.pivot: return False

        self.build_model.scale_active(self.delta_scale, self.pivot, space='v2d', local=self.bbox_model.is_local)
        self.total_scale *= self.delta_scale

        return True

    def calc_both_side(self):
        pivot = self.bbox_model.center
        pivot_r2d = self.bbox_model.center_r2d
        size_x_v2d, size_y_v2d = self.bbox_model.size_v2d

        if self.bbox_model.is_local:
            # rotate the delta vector to the local space
            correct_delta_vec = VecTool.rotate_by_angle(self.delta_vec_v2d, self.bbox_model.rotation_2d())
            delta_x, delta_y = correct_delta_vec.xy
        else:
            delta_x, delta_y = (self.delta_vec_v2d * 2).xy
        if self.mouse_pos[0] < pivot_r2d[0]:  # if on the left side
            delta_x = -delta_x
        if self.mouse_pos[1] < pivot_r2d[1]:  # if on the bottom side
            delta_y = -delta_y

        return pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y

    def calc_one_side(self):
        if self.bbox_model.is_local:
            # rotate the delta vector to the local space
            correct_delta_vec = VecTool.rotate_by_angle(self.delta_vec_v2d, self.bbox_model.rotation_2d())
            delta_x, delta_y = correct_delta_vec.xy
        else:
            delta_x, delta_y = self.delta_vec_v2d.xy
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

        if EdgeCenter.point_on_bottom(self.pt_edge_center) or EdgeCenter.point_on_top(self.pt_edge_center):
            vec_scale = Vector((1, scale_y, 0))
        else:
            vec_scale = Vector((scale_x, 1, 0))

        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.delta_scale = vec_scale

    def both_sides_corner(self, unify_scale: bool):
        pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y = self.calc_both_side()
        if self.pos_corner[0] == self.bbox_model.min_x:
            delta_x = -delta_x
        if self.pos_corner[1] == self.bbox_model.min_y:
            delta_y = -delta_y

        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)
        vec_scale = Vector((scale_x, scale_y, 0))
        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.delta_scale = vec_scale

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
        self.delta_scale = vec_scale

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
        self.delta_scale = vec_scale
