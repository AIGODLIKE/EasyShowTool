import gpu
import gpu.state
import gpu.shader
import bpy
import blf
import numpy as np
import bmesh
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from mathutils import Color, Vector

from typing import Sequence, Union, ClassVar, Literal, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from collections import OrderedDict

from ..public_path import get_pref
from ..model.model_gp_bbox import GreasePencilLayerBBox
from ..model.model_draw import DrawData, DrawPreference
from ..view_model.view_model_drag import DragGreasePencilViewModal
from ..view_model.view_model_draw import DrawViewModel

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices

class ViewDrawHandle():
    handle = None
    func: Union['ViewBasic', Callable]
    log: ClassVar[list[str]] = []

    def add_to_node_editor(self, func: Union['ViewBasic', Callable], args: tuple):
        print('add_to_node_editor', func.__class__.__name__)
        self.log.append('Add: ' + func.__class__.__name__)
        self.func = func
        if self.handle is None:
            self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(func, args, 'WINDOW', 'POST_PIXEL')

    def remove_from_node_editor(self):
        print('remove_from_node_editor', self.func.__class__.__name__)
        if self.handle:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None



@dataclass
class ViewBasic:
    drag_vmodel: DragGreasePencilViewModal
    draw_data: DrawData = field(init=False)
    draw_preference: DrawPreference = field(init=False)
    draw_model: DrawViewModel = field(init=False)
    # show state
    _visible: bool = True

    def __call__(self, *args, **kwargs):
        if self.drag_vmodel.bbox_model.is_empty(): return  # empty data
        if not self._visible: return
        self.update()
        self.draw()

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    def draw(self):
        """override this method to draw the view"""
        ...

    def update(self):
        """override this method to update the draw data"""
        ...


@dataclass
class ViewHover(ViewBasic):

    def __post_init__(self):
        gp_data_bbox: GreasePencilLayerBBox = self.drag_vmodel.bbox_model
        top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
        points = [top_left, top_right, bottom_left, bottom_right]

        self.draw_data = DrawData(points, gp_data_bbox.edge_center_points_r2d)
        self.draw_preference = DrawPreference()
        self.draw_model = DrawViewModel(self.draw_data, self.draw_preference)

    def update(self):
        self.draw_model.update_draw_data(points=self.drag_vmodel.bbox_model.bbox_points_r2d,
                                         edge_points=self.drag_vmodel.bbox_model.edge_center_points_r2d)

    def draw(self) -> None:
        self.draw_model.draw_bbox_edge()

        if self.drag_vmodel.in_drag_area:
            self.draw_model.draw_bbox_edge(highlight=True)
        if self.drag_vmodel.pos_near_edge_center:
            self.draw_model.draw_scale_edge_widget()
        if self.drag_vmodel.pos_near_corner:
            self.draw_model.draw_scale_corner_widget()
        elif self.drag_vmodel.pos_near_corner_extrude:
            self.draw_model.draw_rotate_widget(point=self.drag_vmodel.pos_near_corner_extrude)

        if self.draw_model.debug:
            self.draw_model.draw_debug_info(self.drag_vmodel.debug_info)


@dataclass
class ViewDrag(ViewBasic):
    def __post_init__(self):
        gp_data_bbox: GreasePencilLayerBBox = self.drag_vmodel.bbox_model
        start_pos = Vector(self.drag_vmodel.start_pos)
        end_pos = Vector(self.drag_vmodel.end_pos)
        delta_degree = self.drag_vmodel.delta_degree

        self.draw_data: DrawData = DrawData(gp_data_bbox.bbox_points_r2d, gp_data_bbox.edge_center_points_r2d,
                                            start_pos,
                                            end_pos, delta_degree)
        self.draw_preference = DrawPreference()
        self.draw_model = DrawViewModel(self.draw_data, self.draw_preference)

    def update(self):
        self.draw_model.update_draw_data(points=self.drag_vmodel.bbox_model.bbox_points_r2d,
                                         edge_points=self.drag_vmodel.bbox_model.edge_center_points_r2d,
                                         start_pos=Vector(self.drag_vmodel.start_pos),
                                         end_pos=Vector(self.drag_vmodel.end_pos),
                                         delta_degree=self.drag_vmodel.delta_degree)

    def draw(self) -> None:
        if self.draw_model.drag_area:
            self.draw_model.draw_bbox_area()
        if self.draw_model.drag:
            self.draw_model.draw_bbox_edge()
            self.draw_model.draw_bbox_points()

        if self.draw_model.debug:
            self.draw_model.draw_debug_info(self.drag_vmodel.debug_info)
