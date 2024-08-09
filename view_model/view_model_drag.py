from contextlib import contextmanager
from dataclasses import dataclass, field
from mathutils import Vector
from typing import Literal, Optional, Any, ClassVar
import bpy
from collections import OrderedDict

from .view_model_mouse import MouseDragState
from ..public_path import get_pref
from ..model.model_gp import BuildGreasePencilData
from ..model.model_points import AreaPoint
from ..model.model_gp_bbox import GPencilLayerBBox
from ..view_model.view_model_mouse import MouseDetectModel
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
    drag_handles: dict[Literal['MOVE', 'SCALE', 'ROTATE'], TransformHandler] = field(default_factory=dict)

    # model from gp_data will be created
    bbox_model: GPencilLayerBBox = field(init=False)
    build_model: BuildGreasePencilData = field(init=False)
    detect_model: MouseDetectModel = field(init=False)

    # state / on points
    pos_edge_center: AreaPoint = None
    pos_corner: AreaPoint = None
    pos_corner_extrude: AreaPoint = None
    # mouse
    mouse_state: MouseDragState = field(default_factory=MouseDragState)
    # state
    in_drag_area: bool = False
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

    def set_bbox_mode(self, mode: Literal['GLOBAL', 'LOCAL', 'TOGGLE']):
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
        self.pos_edge_center = res.get('edge_center')
        self.pos_corner = res.get('corner')
        self.pos_corner_extrude = res.get('corner_extrude')
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

    def _update_drag_handles(self, event):
        """Update the change handlers.
        use if elif to handle scale/rotate/move because the order matters.
        """
        self._handle_copy(event)
        pass_in_args: dict[str, Any] = {
            'pos_edge_center': self.pos_edge_center,
            'pos_corner': self.pos_corner,
            'pos_corner_extrude': self.pos_corner_extrude,
            'in_drag_area': self.in_drag_area,
        }
        models = {'bbox_model': self.bbox_model, 'build_model': self.build_model}

        self.debug_info['drag_handle'] = 'None'
        self.select_runtime.hide_select_box()
        self.debug_info['cost_time'] = '0'
        if (self.pos_edge_center or self.pos_corner) and (drag_scale_handler := self.drag_handles.get('SCALE')):
            drag_scale_handler.handle(event=event, mouse_state=self.mouse_state, models=models, **pass_in_args)
            self.debug_info['drag_handle'] = 'Scale'
            self.debug_info['cost_time'] = str(drag_scale_handler.cost_time) + 's'
        elif self.pos_corner_extrude and (drag_rotate_handler := self.drag_handles.get('ROTATE')):
            drag_rotate_handler.handle(event=event, mouse_state=self.mouse_state, models=models, **pass_in_args)
            self.debug_info['drag_handle'] = 'Rotate'
            self.debug_info['cost_time'] = str(drag_rotate_handler.cost_time) + 's'
        elif self.in_drag_area and (drag_move_handler := self.drag_handles.get('MOVE')):
            drag_move_handler.handle(event=event, mouse_state=self.mouse_state, models=models, **pass_in_args)
            self.debug_info['drag_handle'] = 'Move'
            self.debug_info['cost_time'] = str(drag_move_handler.cost_time) + 's'
        else:
            self.select_runtime.show_select_box()
            self._handle_select(event)
            self.debug_info['drag_handle'] = 'Select'

    def _handle_select(self, event):
        # drag box points to detect if a layer is selected
        box_area = self.mouse_state.drag_area()
        box_area_points = box_area.corner_points

        bbox_model = GPencilLayerBBox(self.gp_data)
        bbox_model.mode = self.bbox_model.mode
        detect_model = MouseDetectModel().bind_bbox(bbox_model)
        for layer in self.gp_data.layers:
            bbox_model.calc_bbox(layer.info)
            if detect_model.bbox_in_area(box_area_points):
                if not event.ctrl:  # add / update
                    points = list(bbox_model.bbox_points_v2d)
                    points[2], points[3] = points[3], points[2]
                    self.select_runtime.update(layer.info, points)
                else:  # remove
                    self.select_runtime.remove(layer.info)
        # clear the selected layers if no layer is selected
        if not (event.shift or event.ctrl) and not self.select_runtime.selected_layers():
            self.select_runtime.clear()
        # if only one layer is selected, set it to active
        if len(self.select_runtime.selected_layers()) == 1:
            self.build_model.set_active_layer(self.select_runtime.selected_layers()[0])

    def clear_selected_layers_points(self):
        self.select_runtime.clear()

    def _update_active_bbox(self, context):
        """Update the Grease Pencil Data. Some data may be changed in the modal."""
        if self.build_model.is_empty():
            return

        if self.build_model.active_layer is None:
            return

        self.bbox_model.calc_active_layer_bbox()
        _ = self.bbox_model.bbox_points_3d  # update the bbox points
