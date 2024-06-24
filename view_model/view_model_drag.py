from dataclasses import dataclass, field
from mathutils import Vector
from typing import Literal, Optional, Callable, Final, Any
import bpy
from collections import OrderedDict

from ..public_path import get_pref
from ..model.model_gp import VecTool, BuildGreasePencilData
from ..model.model_gp_bbox import GreasePencilLayerBBox
from ..view_model.view_model_detect import MouseDetectModel
from .handlers import TransformHandler


@dataclass
class DragGreasePencilViewModal:
    # need to pass in
    gp_data: bpy.types.GreasePencil
    # callback
    on_mouse_init: list[Callable] = field(default_factory=list)
    on_mouse_move: list[Callable] = field(default_factory=list)
    # drag_handle
    drag_scale_handler: Optional[TransformHandler] = None
    drag_move_handler: Optional[TransformHandler] = None
    drag_rotate_handler: Optional[TransformHandler] = None
    # model from gp_data will be created
    bbox_model: GreasePencilLayerBBox = field(init=False)
    build_model: BuildGreasePencilData = field(init=False)
    detect_model: MouseDetectModel = field(init=False)
    # state / on points
    pos_edge_center: Vector = None
    pos_corner: Vector = None
    pos_corner_extrude: Vector = None
    pt_corner: int = 0
    pt_edge_center: int = 0
    pt_corner_extrude: int = 0
    # mouse
    mouse_pos: tuple[int, int] = (0, 0)
    mouse_pos_prev: tuple[int, int] = (0, 0)
    start_pos: tuple[int, int] = (0, 0)
    start_center_pos: tuple[int, int] = (0, 0)
    end_pos: tuple[int, int] = (0, 0)
    delta_vec_v2d: Vector = Vector((0, 0))
    # state
    in_drag_area: bool = False
    # snap
    snap_degree: int = field(default_factory=lambda: get_pref().gp_behavior.snap_degree)
    # copy
    already_copied: bool = False
    # debug
    debug: bool = field(default_factory=lambda: get_pref().debug)
    debug_info: OrderedDict[str, str] = field(default_factory=OrderedDict)

    def __post_init__(self):
        self.bbox_model = GreasePencilLayerBBox(self.gp_data)
        self.build_model = BuildGreasePencilData(self.gp_data)
        self.detect_model = MouseDetectModel().bind_bbox(self.bbox_model)

    def has_active_layer(self) -> bool:
        return self.build_model.has_active_layer()

    def handle_drag(self, context, event):
        """Handle the drag event in the modal."""
        self._update_drag_handles(event)

    def update_near_widgets(self):
        """Detect and update the near points and areas of the Grease Pencil Object."""
        # TODO this event will not show at a same time , so make it to if  branch

        res = self.detect_model.detect_near(self.mouse_pos)
        self.pos_edge_center, self.pt_edge_center = res.get('edge_center')
        self.pos_corner, self.pt_corner = res.get('corner')
        self.pos_corner_extrude, self.pt_corner_extrude = res.get('corner_extrude')
        self.in_drag_area = res.get('in_area')

        if self.debug:
            self.debug_info['pos_edge_center'] = str(self.pos_edge_center)
            self.debug_info['pos_corner'] = str(self.pos_corner)
            self.debug_info['pos_corner_extrude'] = str(self.pos_corner_extrude)
            self.debug_info['in_drag_area'] = str(self.in_drag_area)

    def mouse_init(self):
        self.start_pos = self.mouse_pos
        for callback in self.on_mouse_init:
            callback()

    def update_mouse_pos(self, context, event):
        """Update the mouse position and the delta vector. Prepare for the handle_drag."""
        self.mouse_pos_prev = self.mouse_pos
        self.mouse_pos = event.mouse_region_x, event.mouse_region_y
        self.end_pos = self.mouse_pos
        self._update_bbox(context)
        pre_v2d = VecTool.r2d_2_v2d(self.mouse_pos_prev)
        cur_v2d = VecTool.r2d_2_v2d(self.mouse_pos)
        self.delta_vec_v2d = Vector((cur_v2d[0] - pre_v2d[0], cur_v2d[1] - pre_v2d[1]))

        for callback in self.on_mouse_move:
            callback()

        if self.debug:
            self.debug_info['mouse_pos'] = str(self.mouse_pos)
            self.debug_info['mouse_pos_prev'] = str(self.mouse_pos_prev)
            self.debug_info['start_pos'] = str(self.start_pos)
            self.debug_info['end_pos'] = str(self.end_pos)

    def _handle_copy(self, event):
        """Handle the copy event in the modal."""
        if not self.already_copied and event.alt:
            with self.build_model:  # clean up in with statement
                self.build_model.copy_active().to_2d()
                self.already_copied = True

    def _collect_kwargs(self) -> dict[str, Any]:
        return {
            k: getattr(self, k) for k in self.__dict__ if
            k not in {'drag_scale_handler', 'drag_move_handler', 'drag_rotate_handler', 'gp_data', 'bbox_model',
                      'build_model', 'detect_model'}
        }

    def _update_drag_handles(self, event):
        """Update the change handlers.
        use if elif to handle scale/rotate/move because the order matters.
        """
        self._handle_copy(event)
        pass_in_args = self._collect_kwargs()
        models = {'bbox_model': self.bbox_model, 'build_model': self.build_model}

        if (self.pos_edge_center or self.pos_corner) and self.drag_scale_handler:
            self.drag_scale_handler.handle(event=event, models=models, **pass_in_args)
        elif self.pos_corner_extrude and self.drag_rotate_handler:
            self.drag_rotate_handler.handle(event=event, models=models, **pass_in_args)
        elif self.in_drag_area and self.drag_move_handler:
            self.drag_move_handler.handle(event=event, models=models, **pass_in_args)

    def _update_bbox(self, context):
        """Update the Grease Pencil Data. Some data may be changed in the modal."""
        if self.build_model.is_empty():
            return

        if self.build_model.active_layer is None:
            return

        self.bbox_model.calc_active_layer_bbox()
        _ = self.bbox_model.bbox_points_3d
