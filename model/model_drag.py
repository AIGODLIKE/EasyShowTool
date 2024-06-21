from dataclasses import dataclass, field
from mathutils import Vector
from math import degrees
from typing import Literal
from typing import Optional
import bpy

from ..public_path import get_pref
from .utils import Coord, EdgeCenter
from .model_gp import VecTool, BuildGreasePencilData
from .model_gp_bbox import GreasePencilLayerBBox, MouseDetectModel


@dataclass
class DragGreasePencilModel:
    gp_data: bpy.types.GreasePencil
    bbox_model: GreasePencilLayerBBox = field(init=False)
    build_model: BuildGreasePencilData = field(init=False)
    detect_model: MouseDetectModel = field(init=False)
    # mouse
    mouse_pos: tuple[int, int] = (0, 0)
    mouse_pos_prev: tuple[int, int] = (0, 0)
    delta_vec: Vector = Vector((0, 0))
    # state / on points
    on_edge_center: Vector = None
    pt_edge_center: int = 0
    on_corner: Vector = None
    pt_corner: int = 0
    on_corner_extrude: Vector = None
    pt_corner_extrude: int = 0
    # state
    in_drag_area: bool = False
    # pref, detect edge
    d_edge: int = field(default_factory=lambda: get_pref().gp_detect_edge_px)
    d_corner: int = field(default_factory=lambda: get_pref().gp_detect_corner_px)
    d_rotate: int = field(default_factory=lambda: get_pref().gp_detect_rotate_px)
    # snap
    snap_degree: int = field(default_factory=lambda: get_pref().gp_snap_degree)
    delta_degree: float = 0
    # copy
    already_copied: bool = False

    def __post_init__(self):
        self.bbox_model = GreasePencilLayerBBox(self.gp_data)
        self.build_model = BuildGreasePencilData(self.gp_data)
        self.detect_model = self.bbox_model.detect_model

    def handle_drag(self, context, event):
        """Handle the drag event in the modal."""
        # scale mode
        if self.on_edge_center or self.on_corner:  # scale only when near point
            if event.ctrl:
                self.on_drag_scale_both_side(event)
            else:
                self.on_drag_scale_one_side(event)
        # rotate mode
        elif self.on_corner_extrude:
            self.on_drag_rotate(event)
        # move mode
        elif self.in_drag_area:
            self.handle_copy(event)
            self.on_drag_move()

    def handle_copy(self, event):
        """Handle the copy event in the modal."""
        if not self.already_copied and event.alt:
            with self.build_model:  # clean up in with statement
                self.build_model.copy_active().to_2d()
                self.already_copied = True

    def update_mouse_pos(self, context, event):
        """Update the mouse position and the delta vector. Prepare for the handle_drag."""
        self.mouse_pos_prev = self.mouse_pos
        self.mouse_pos = event.mouse_region_x, event.mouse_region_y
        self.update_gp_data(context)
        pre_v2d = VecTool.r2d_2_v2d(self.mouse_pos_prev)
        cur_v2d = VecTool.r2d_2_v2d(self.mouse_pos)
        self.delta_vec = Vector((cur_v2d[0] - pre_v2d[0], cur_v2d[1] - pre_v2d[1]))

    def on_drag_scale_both_side(self, event):
        """Scale the active layer of the Grease Pencil Object when near the edge center or corner."""
        pivot = self.bbox_model.center
        pivot_r2d = self.bbox_model.center_r2d
        size_x_v2d, size_y_v2d = self.bbox_model.size_v2d

        delta_x, delta_y = (self.delta_vec * 2).xy
        if self.mouse_pos[0] < pivot_r2d[0]:  # if on the left side
            delta_x = -delta_x
        if self.mouse_pos[1] < pivot_r2d[1]:  # if on the bottom side
            delta_y = -delta_y

        if self.on_edge_center:  # scale only one axis

            scale_x = 1 + delta_x / size_x_v2d
            scale_y = 1 + delta_y / size_y_v2d

            if self.on_edge_center[0] == pivot_r2d[0]:
                vec_scale = Vector((1, scale_y, 0))
            else:
                vec_scale = Vector((scale_x, 1, 0))
        else:  # scale both axis
            if self.on_corner[0] == self.bbox_model.min_x:
                delta_x = -delta_x
            if self.on_corner[1] == self.bbox_model.min_y:
                delta_y = -delta_y

            scale_x = 1 + delta_x / size_x_v2d
            scale_y = 1 + delta_y / size_y_v2d

            unit_scale = scale_x if abs(delta_x) > abs(delta_y) else scale_y  # scale by the larger delta
            vec_scale = Vector((unit_scale, unit_scale, 0)) if event.shift else Vector(
                (scale_x, scale_y, 0))

        self.build_model.scale_active(vec_scale, pivot, space='3d')

    def on_drag_scale_one_side(self, event):
        delta_x, delta_y = self.delta_vec.xy
        size_x_v2d, size_y_v2d = self.bbox_model.size_v2d

        if self.on_corner:
            points = self.bbox_model.bbox_points_3d
            pivot_index = Coord.opposite(self.pt_corner)
            pivot = points[pivot_index]

            if Coord.point_on_left(self.pt_corner):
                delta_x = -delta_x
            if Coord.point_on_bottom(self.pt_corner):
                delta_y = -delta_y

            scale_x = 1 + delta_x / size_x_v2d
            scale_y = 1 + delta_y / size_y_v2d

            vec_scale = Vector((scale_x, scale_y, 0))

        elif self.on_edge_center:
            points = self.bbox_model.edge_center_points_3d
            pivot_index = EdgeCenter.opposite(self.pt_edge_center)
            pivot: Vector = points[pivot_index]

            if EdgeCenter.point_on_left(self.pt_edge_center):
                delta_x = -delta_x
            if EdgeCenter.point_on_bottom(self.pt_edge_center):
                delta_y = -delta_y

            scale_x = 1 + delta_x / size_x_v2d
            scale_y = 1 + delta_y / size_y_v2d

            vec_scale = Vector((scale_x, scale_y, 0))
        else:
            vec_scale = None
            pivot = None

        if vec_scale is None: return
        if event.shift:
            if abs(delta_x) > abs(delta_y):
                vec_scale.y = vec_scale.x
            else:
                vec_scale.x = vec_scale.y

        self.build_model.scale_active(vec_scale, pivot, space='3d')

    def on_drag_rotate(self, event):
        """Rotate the active layer of the Grease Pencil Object when near the corner extrude point."""
        pivot = self.bbox_model.center
        pivot_r2d = self.bbox_model.center_r2d

        vec_1 = (Vector(self.mouse_pos) - Vector(pivot_r2d))
        vec_2 = Vector(self.mouse_pos_prev) - Vector(pivot_r2d)
        # clockwise or counterclockwise
        inverse: Literal[1, -1] = VecTool.rotation_direction(vec_1, vec_2)
        angle = inverse * vec_1.angle(vec_2)
        degree = degrees(angle)
        # snap
        if not event.shift:
            self.build_model.rotate_active(degree, pivot)
        else:
            self.delta_degree += abs(degree)
            if self.delta_degree > self.snap_degree:
                self.delta_degree = 0
                self.build_model.rotate_active(self.snap_degree * inverse, pivot)

    def on_drag_move(self):
        # move only when in drag area
        self.build_model.move_active(self.delta_vec, space='v2d')

    def detect_near_widgets(self):
        """Detect the near points and areas of the Grease Pencil Object."""
        self.on_edge_center, self.pt_edge_center = self.detect_model.near_edge_center(self.mouse_pos,
                                                                                      radius=self.d_edge)
        self.on_corner, self.pt_corner = self.detect_model.near_corners(self.mouse_pos, radius=self.d_corner)
        self.on_corner_extrude, self.pt_corner_extrude = self.detect_model.near_corners_extrude(self.mouse_pos,
                                                                                                extrude=20,
                                                                                                radius=self.d_rotate)
        self.in_drag_area = self.detect_model.in_area(self.mouse_pos, feather=0)

    def update_gp_data(self, context):
        """Update the Grease Pencil Data. Some data may be changed in the modal."""
        if self.build_model.is_empty():
            return

        if self.build_model.active_layer is None:
            return

        self.bbox_model.calc_active_layer_bbox()
        _ = self.bbox_model.bbox_points_3d
