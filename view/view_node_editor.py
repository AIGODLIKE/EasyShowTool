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

from typing import Sequence, Union, ClassVar, Literal, Optional
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


# TODO refactor view classes
@dataclass
class ViewHover():
    drag_vmodel: DragGreasePencilViewModal
    draw_data: DrawData = field(init=False)
    draw_preference: DrawPreference = field(init=False)
    draw_model: DrawViewModel = field(init=False)

    def __post_init__(self):
        gp_data_bbox: GreasePencilLayerBBox = self.drag_vmodel.bbox_model
        top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
        points = [top_left, top_right, bottom_left, bottom_right]
        coords = [top_left, top_right, bottom_right, bottom_left, top_left]  # close the loop

        self.draw_data = DrawData(points, gp_data_bbox.edge_center_points_r2d, coords)
        self.draw_preference = DrawPreference()
        self.draw_model = DrawViewModel(self.draw_data, self.draw_preference)

    def __call__(self, *args, **kwargs):
        self.draw_hover_callback_px()

    def is_empty(self):
        return self.drag_vmodel.bbox_model.is_empty()

    def draw_hover_callback_px(self) -> None:
        if self.is_empty(): return  # empty data

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


class ViewDrag():
    def __call__(self, *args, **kwargs):
        self.draw_drag_callback_px(*args, **kwargs)

    def draw_drag_callback_px(self, drag_vmodel: DragGreasePencilViewModal, context) -> None:
        gp_data_bbox: GreasePencilLayerBBox = drag_vmodel.bbox_model
        if gp_data_bbox.is_empty(): return  # empty data

        start_pos = Vector(drag_vmodel.start_pos)
        end_pos = Vector(drag_vmodel.end_pos)
        delta_degree = drag_vmodel.delta_degree

        top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
        points = [top_left, top_right, bottom_left, bottom_right]
        coords = [top_left, top_right, bottom_right, bottom_left, top_left]  # close the loop

        draw_model: DrawViewModel = DrawViewModel(points, gp_data_bbox.edge_center_points_r2d, coords, start_pos,
                                                  end_pos,
                                                  delta_degree)

        if draw_model.drag_area:
            draw_model.draw_bbox_area()
        if draw_model.drag:
            draw_model.draw_bbox_edge()
            draw_model.draw_bbox_points()

        if draw_model.debug:
            draw_model.draw_debug_info(drag_vmodel.debug_info)
