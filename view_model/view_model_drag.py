from contextlib import contextmanager
from dataclasses import dataclass, field
from mathutils import Vector
from typing import Literal, Optional, Any, ClassVar
import bpy
from collections import OrderedDict

from .view_model_detect import MouseState
from ..public_path import get_pref
from ..model.model_gp import BuildGreasePencilData
from ..model.model_gp_bbox import GPencilLayerBBox
from ..view_model.view_model_detect import MouseDetectModel
from .view_model_select import SelectedGPLayersRuntime
from .handlers import TransformHandler


@dataclass
class DragGreasePencilViewModal:
    # need to pass in
    gp_data: bpy.types.GreasePencil
    last_gp_data: ClassVar[bpy.types.GreasePencil] = None
    #
    select_runtime: SelectedGPLayersRuntime = SelectedGPLayersRuntime()
    # drag_handle
    drag_handle: dict[Literal['MOVE', 'SCALE', 'ROTATE'], TransformHandler] = field(default_factory=dict)

    # model from gp_data will be created
    bbox_model: GPencilLayerBBox = field(init=False)
    build_model: BuildGreasePencilData = field(init=False)
    detect_model: MouseDetectModel = field(init=False)
    # callback

    # state / on points
    pos_edge_center: Vector = None
    pos_corner: Vector = None
    pos_corner_extrude: Vector = None
    pt_corner: int = 0
    pt_edge_center: int = 0
    pt_corner_extrude: int = 0
    # mouse
    mouse_state: MouseState = field(default_factory=MouseState)
    # state
    in_drag_area: bool = False
    # snap
    snap_degree: int = field(default_factory=lambda: get_pref().gp_performance.snap_degree)
    # copy
    already_copied: bool = False
    # debug
    debug: bool = field(default_factory=lambda: get_pref().debug)
    debug_info: OrderedDict[str, str] = field(default_factory=OrderedDict)

    def __post_init__(self):
        self.bbox_model = GPencilLayerBBox(self.gp_data)
        self.build_model = BuildGreasePencilData(self.gp_data)
        self.detect_model = MouseDetectModel().bind_bbox(self.bbox_model)

        if self.__class__.last_gp_data is None:
            self.__class__.last_gp_data = self.gp_data
        elif self.__class__.last_gp_data != self.gp_data:
            self.__class__.last_gp_data = self.gp_data
            self.__class__.clear_selected_layers_points(self)

    def has_active_layer(self) -> bool:
        return self.build_model.has_active_layer()

    def set_bbox_mode(self, mode: Literal['GLOBAL', 'LOCAL,', 'TOGGLE']):
        if mode == 'GLOBAL':
            self.bbox_model.to_global()
        elif mode == 'LOCAL':
            self.bbox_model.to_local()
        else:
            if self.bbox_model.is_local:
                self.bbox_model.to_global()
            else:
                self.bbox_model.to_local()

    def handle_drag(self, context, event):
        """Handle the drag event in the modal."""
        self._update_drag_handles(event)

    def update_near_widgets(self):
        """Detect and update the near points and areas of the Grease Pencil Object."""
        # TODO this event will not show at a same time , so make it to if  branch

        res = self.detect_model.detect_near(self.mouse_state.mouse_pos)
        self.pos_edge_center, self.pt_edge_center = res.get('edge_center')
        self.pos_corner, self.pt_corner = res.get('corner')
        self.pos_corner_extrude, self.pt_corner_extrude = res.get('corner_extrude')
        self.in_drag_area = res.get('in_area')

        if self.debug:
            self.debug_info['pos_edge_center'] = str(self.pos_edge_center)
            self.debug_info['pos_corner'] = str(self.pos_corner)
            self.debug_info['pos_corner_extrude'] = str(self.pos_corner_extrude)
            self.debug_info['in_drag_area'] = str(self.in_drag_area)

    def mouse_init(self, event):
        self.mouse_state.init(event)

    def update_mouse_pos(self, context, event):
        """Update the mouse position and the delta vector. Prepare for the handle_drag."""
        self.mouse_state.update_mouse_position(event)
        self._update_active_bbox(context)

        if self.debug:
            self.debug_info['mouse_pos'] = str(self.mouse_state.mouse_pos)
            self.debug_info['mouse_pos_prev'] = str(self.mouse_state.mouse_pos_prev)
            self.debug_info['start_pos'] = str(self.mouse_state.start_pos)
            self.debug_info['end_pos'] = str(self.mouse_state.end_pos)

    def _handle_copy(self, event):
        """Handle the copy event in the modal."""
        if not self.already_copied and event.alt:
            with self.keep_context_select():
                with self.build_model:  # clean up in with statement
                    self.build_model.copy_active().to_2d()
                    self.already_copied = True

    @staticmethod
    @contextmanager
    def keep_context_select():
        if ori_obj := bpy.context.object:
            ori_obj.select_set(True)
        yield
        if ori_obj:
            bpy.context.view_layer.objects.active = ori_obj
            ori_obj.select_set(True)

    def _collect_kwargs(self) -> dict[str, Any]:
        return {
            k: getattr(self, k) for k in self.__dict__ if
            k not in {'drag_scale_handler', 'drag_move_handler', 'drag_rotate_handler', 'gp_data', 'bbox_model',
                      'build_model', 'detect_model', 'mouse_state'}
        }

    def _update_drag_handles(self, event):
        """Update the change handlers.
        use if elif to handle scale/rotate/move because the order matters.
        """
        self._handle_copy(event)
        pass_in_args = self._collect_kwargs()
        models = {'bbox_model': self.bbox_model, 'build_model': self.build_model}

        self.debug_info['drag_handle'] = 'None'
        self.select_runtime.hide_select_box()
        if (self.pos_edge_center or self.pos_corner) and (drag_scale_handler := self.drag_handle.get('SCALE')):
            drag_scale_handler.handle(event=event, mouse_state=self.mouse_state, models=models, **pass_in_args)
            if self.debug:
                self.debug_info['drag_handle'] = 'Scale'
        elif self.pos_corner_extrude and (drag_rotate_handler := self.drag_handle.get('ROTATE')):
            drag_rotate_handler.handle(event=event, mouse_state=self.mouse_state, models=models, **pass_in_args)
            if self.debug:
                self.debug_info['drag_handle'] = 'Rotate'
        elif self.in_drag_area and (drag_move_handler := self.drag_handle.get('MOVE')):
            drag_move_handler.handle(event=event, mouse_state=self.mouse_state, models=models, **pass_in_args)
            if self.debug:
                self.debug_info['drag_handle'] = 'Move'

        else:
            self.select_runtime.show_select_box()
            if self.debug:
                self.debug_info['drag_handle'] = 'Select'
            self._handle_select()

    def _handle_select(self):
        # drag box points to detect if a layer is selected
        box_area_points = self.mouse_state.drag_area()

        bbox_model = GPencilLayerBBox(self.gp_data)
        bbox_model.mode = self.bbox_model.mode
        detect_model = MouseDetectModel().bind_bbox(bbox_model)
        self.select_runtime.clear()
        for layer in self.gp_data.layers:
            bbox_model.calc_bbox(layer.info)
            if detect_model.bbox_in_area(box_area_points):
                points = list(bbox_model.bbox_points_v2d)
                points[2], points[3] = points[3], points[2]
                self.select_runtime.update(layer.info, points)

        # print(self.select_runtime.selected_layers())

    def clear_selected_layers_points(self):
        self.select_runtime.clear()

    def _update_active_bbox(self, context):
        """Update the Grease Pencil Data. Some data may be changed in the modal."""
        if self.build_model.is_empty():
            return

        if self.build_model.active_layer is None:
            return

        self.bbox_model.calc_active_layer_bbox()
        _ = self.bbox_model.bbox_points_3d
