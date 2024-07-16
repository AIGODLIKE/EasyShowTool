from typing import ClassVar
from mathutils import Vector
from ..model.utils import VecTool


class SelectedGPLayersRuntime:
    selected_layers_points_v2d: ClassVar[dict[str, list[Vector]]] = {}

    @classmethod
    def update(cls, layer: str, points: list[Vector]):
        cls.selected_layers_points_v2d[layer] = points

    @classmethod
    def remove(cls, layer: str):
        cls.selected_layers_points_v2d.pop(layer)

    @classmethod
    def clear(cls):
        cls.selected_layers_points_v2d.clear()

    def get_selected_layers_points_r2d(self) -> list[list[Vector]]:
        return [[VecTool.v2d_2_r2d(p) for p in points] for points in self.selected_layers_points_v2d.values()]

    @classmethod
    def selected_layers(cls) -> list[str]:
        return list(cls.selected_layers_points_v2d.keys())