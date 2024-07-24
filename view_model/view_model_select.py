from typing import ClassVar, Literal

import bpy.types
from mathutils import Vector
from ..model.utils import VecTool
from ..model.model_gp_bbox import GPencilLayerBBox


class SelectedGPLayersRuntime:
    draw_select_box: ClassVar[bool] = True  # draw the select box, disable it when the user is dragging
    selected_layers_points_v2d: ClassVar[dict[str, list[Vector]]] = {}

    @classmethod
    def update(cls, layer: str, points: list[Vector]):
        cls.selected_layers_points_v2d[layer] = points

    @classmethod
    def show_select_box(cls):
        cls.draw_select_box = True

    @classmethod
    def hide_select_box(cls):
        cls.draw_select_box = False

    @classmethod
    def remove(cls, layer: str):
        cls.selected_layers_points_v2d.pop(layer)

    @classmethod
    def clear(cls):
        cls.selected_layers_points_v2d.clear()

    @classmethod
    def get_selected_layers_points_r2d(cls) -> list[list[Vector]]:
        return [[VecTool.v2d_2_r2d(p) for p in points] for points in cls.selected_layers_points_v2d.values()]

    @classmethod
    def selected_layers(cls) -> list[str]:
        return list(cls.selected_layers_points_v2d.keys())

    @classmethod
    def update_from_gp_data(cls, gp_data: bpy.types.GreasePencil, mode: Literal['GLOBAL', 'LOCAL'] = 'GLOBAL'):
        bbox_model = GPencilLayerBBox(gp_data, mode=mode)
        for layer_name in cls.selected_layers_points_v2d.keys():
            bbox_model.calc_bbox(layer_name)
            points = list(bbox_model.bbox_points_v2d)
            points[2], points[3] = points[3], points[2]  # swap the bottom left and bottom right
            cls.update(layer_name, points)
