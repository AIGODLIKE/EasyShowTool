from dataclasses import dataclass
from typing import Callable, Optional, Literal
import bpy
from math import degrees
from mathutils import Vector

from ..model.utils import Coord, EdgeCenter, VecTool
from ..model.model_gp_bbox import GPencilLayerBBox, GPencilLayersBBox
from ..model.model_gp import BuildGreasePencilData
from ..model.model_points import AreaPoint
from .view_model_mouse import MouseDragState


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

    def is_on_region_edge(self, mouse_pos: Vector) -> bool:
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
    bbox_model: GPencilLayerBBox | None = None  # init by drag modal
    build_model: BuildGreasePencilData | None = None  # init by drag modal
    # callback
    call_before: Optional[Callable] = None
    call_after: Optional[Callable] = None
    # use for multi-layer
    selected_layers: list[str] = None
    # mouse
    mouse_state: MouseDragState = None

    def accept_event(self, event: bpy.types.Event) -> bool:
        ...  # subclass should implement this method

    def handle(self, event: bpy.types.Event, mouse_state: MouseDragState, models: Optional[dict] = None,
               **kwargs) -> bool:
        # if key in self.__dict__: # set the attribute
        if self.mouse_state is None:
            self.mouse_state = mouse_state
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
        return True


@dataclass
class MoveHandler(TransformHandler):
    # state
    total_move: Vector = Vector((0, 0))  # value between the last mouse move and the first mouse move
    delta_move: Vector = None  # compare to the last mouse move
    # in

    view_pan: ViewPan = None

    def __post_init__(self):
        self.view_pan = ViewPan()

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the move event in the modal."""
        delta_vec_v2d = self.mouse_state.delta_vec_v2d
        end_pos = self.mouse_state.end_pos
        if not delta_vec_v2d:
            return False
        if not self.selected_layers:
            self.build_model.move_active(delta_vec_v2d, space='v2d')
        else:
            for layer in self.selected_layers:
                self.build_model.move(layer, delta_vec_v2d, space='v2d')
        self.delta_move = delta_vec_v2d
        self.total_move += delta_vec_v2d
        if self.view_pan.is_on_region_edge(end_pos):
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
    snap_degree: int = 0
    snap_degree_count: int = 0

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the rotate event in the modal."""
        if not self.pivot:
            if not self.selected_layers:
                self.pivot = self.bbox_model.center_v2d
                self.pivot_r2d = self.bbox_model.center_r2d
            else:
                layers_bbox = GPencilLayersBBox(self.bbox_model.gp_data)
                layers_bbox.calc_multiple_layers_bbox(self.selected_layers)
                self.pivot = layers_bbox.center_v2d
                self.pivot_r2d = layers_bbox.center_r2d

        inverse, angle = self.mouse_state.get_rotate_delta_angle(self.pivot_r2d)
        degree = degrees(angle)

        # snap
        if not event.shift:
            self.delta_degree += degree
            if self.selected_layers:
                for layer in self.selected_layers:
                    self.build_model.rotate(layer, degree, self.pivot, space='v2d')
            else:
                self.build_model.rotate_active(degree, self.pivot, space='v2d')
            self.total_degree += degree
        else:
            self.snap_degree_count += abs(degree)
            if self.snap_degree_count > self.snap_degree:
                self.snap_degree_count = 0
                self.delta_degree += self.snap_degree * inverse
                if self.selected_layers:
                    for layer in self.selected_layers:
                        self.build_model.rotate(layer, self.snap_degree * inverse, self.pivot, space='v2d')
                else:
                    self.build_model.rotate_active(self.snap_degree * inverse, self.pivot, space='v2d')
                self.total_degree += self.snap_degree * inverse
        return True


@dataclass
class ScaleHandler(TransformHandler):
    # state
    total_scale: Vector = Vector((1, 1, 1))
    delta_scale: Vector = None
    pivot: Vector = None
    pivot_local: Vector = None
    degree_local: float = 0

    # pass in
    pos_edge_center: AreaPoint | None = None
    pos_corner: AreaPoint | None = None

    def accept_event(self, event: bpy.types.Event) -> bool:
        """Handle the scale event in the modal.
        :return: True if the scale is handled, False otherwise. Event will be accepted if True."""
        unify_scale = event.shift
        center_scale = event.ctrl

        self.delta_vec_v2d = self.mouse_state.delta_vec_v2d
        self.mouse_pos = self.mouse_state.mouse_pos

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

    def calc_both_side(self) -> tuple[Vector, Vector, float, float, float, float]:
        pivot = self.bbox_model.center
        pivot_r2d = self.bbox_model.center_r2d
        size_x_v2d, size_y_v2d = self.bbox_model.size_v2d

        if self.bbox_model.is_local:
            # rotate the delta vector to the local space
            correct_delta_vec = VecTool.rotate_by_angle(self.delta_vec_v2d, self.bbox_model.layer_rotate_2d())
            delta_x, delta_y = correct_delta_vec.xy
        else:
            delta_x, delta_y = (self.delta_vec_v2d * 2).xy
        if self.mouse_pos[0] < pivot_r2d[0]:  # if on the left side
            delta_x = -delta_x
        if self.mouse_pos[1] < pivot_r2d[1]:  # if on the bottom side
            delta_y = -delta_y

        return pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y

    def calc_one_side(self) -> tuple[float, float, float, float]:
        if self.bbox_model.is_local:
            # rotate the delta vector to the local space
            correct_delta_vec = VecTool.rotate_by_angle(self.delta_vec_v2d, self.bbox_model.layer_rotate_2d())
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

    def both_sides_edge_center(self, unify_scale: bool) -> None:
        pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y = self.calc_both_side()
        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)

        if 'top' in self.pos_edge_center.position_type or 'bottom' in self.pos_edge_center.position_type:
            vec_scale = Vector((1, scale_y, 0))
        else:
            vec_scale = Vector((scale_x, 1, 0))

        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.delta_scale = vec_scale

    def both_sides_corner(self, unify_scale: bool) -> None:
        pivot, pivot_r2d, size_x_v2d, size_y_v2d, delta_x, delta_y = self.calc_both_side()
        if self.pos_corner.x == self.bbox_model.min_x:
            delta_x = -delta_x
        if self.pos_corner.y == self.bbox_model.min_y:
            delta_y = -delta_y

        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)
        vec_scale = Vector((scale_x, scale_y, 0))
        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.delta_scale = vec_scale

    def one_side_edge_center(self, unify_scale: bool) -> None:
        delta_x, delta_y, size_x_v2d, size_y_v2d = self.calc_one_side()
        points = self.bbox_model.edge_center_points_3d  # top_center, right_center, bottom_center, left_center
        match self.pos_edge_center.position_type:
            case 'top_center':
                pivot = points[2]
            case 'right_center':
                pivot = points[3]
            case 'bottom_center':
                pivot = points[0]
            case 'left_center':
                pivot = points[1]
            case _:
                raise ValueError(f"Invalid position type: {self.pos_edge_center.position_type}")

        if 'left' in self.pos_edge_center.position_type:
            delta_x = -delta_x
        if 'bottom' in self.pos_edge_center.position_type:
            delta_y = -delta_y

        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)

        if 'left' in self.pos_edge_center.position_type or 'right' in self.pos_edge_center.position_type:
            vec_scale = Vector((scale_x, 1, 0))
        else:
            vec_scale = Vector((1, scale_y, 0))

        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.delta_scale = vec_scale

    def one_side_corner(self, unify_scale: bool) -> None:
        delta_x, delta_y, size_x_v2d, size_y_v2d = self.calc_one_side()
        points = self.bbox_model.bbox_points_3d  # top_left, top_right, bottom_left, bottom_right
        match self.pos_corner.position_type:
            case 'top_left':
                pivot = points[3]
            case 'top_right':
                pivot = points[2]
            case 'bottom_left':
                pivot = points[1]
            case 'bottom_right':
                pivot = points[0]
            case _:
                raise ValueError(f"Invalid position type: {self.pos_corner.position_type}")

        if 'left' in self.pos_corner.position_type:
            delta_x = -delta_x
        if 'bottom' in self.pos_corner.position_type:
            delta_y = -delta_y

        scale_x, scale_y = self.calc_scale(delta_x, delta_y, size_x_v2d, size_y_v2d)

        vec_scale = Vector((scale_x, scale_y, 0))
        if unify_scale:
            self.unify_scale(delta_x, delta_y, vec_scale)

        self.pivot = pivot
        self.delta_scale = vec_scale
