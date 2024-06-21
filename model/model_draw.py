import gpu
import gpu.state
import gpu.shader
import bpy
from mathutils import Color, Vector
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from typing import Sequence, Union, ClassVar

from .model_gp import GreasePencilLayerBBox
from ..public_path import get_pref

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices

from dataclasses import dataclass, field


@dataclass
class DrawModel():
    # data
    points: Sequence[Vector, Vector, Vector, Vector]
    edge_points: Sequence[Vector, Vector, Vector, Vector]
    coords: Sequence[Vector, Vector, Vector, Vector, Vector]  # close the loop, for drawing lines

    # default
    debug_color: Color = Color((0, 1, 0, 0.5))
    point_size: ClassVar[int] = 20
    # pref
    line_width: int = get_pref().gp_draw_line_width
    debug: bool = get_pref().debug_draw
    drag: bool = get_pref().gp_draw_drag
    drag_area: bool = get_pref().gp_draw_drag_area
    color: Color = get_pref().gp_color
    color_hover: Color = get_pref().gp_color_hover
    color_area: Color = get_pref().gp_color_area
    # detect
    corner_px: int = get_pref().gp_detect_corner_px
    edge_px: int = get_pref().gp_detect_edge_px
    rotate_px: int = get_pref().gp_detect_rotate_px

    def __post_init__(self):
        gpu.state.line_width_set(self.line_width)
        gpu.state.point_size_set(self.point_size)
        gpu.state.blend_set('ALPHA')

    def draw_bbox_points(self):
        shader.uniform_float("color", self.color)
        batch = batch_for_shader(shader, 'POINTS', {"pos": self.points})
        batch.draw(shader)

    def draw_bbox_edge(self):
        gpu.state.point_size_set(10)
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": self.coords})
        shader.uniform_float("color", self.color)
        batch.draw(shader)

    def draw_bbox_area(self):
        shader.uniform_float("color", self.color_area)
        batch = batch_for_shader(shader, 'TRIS', {"pos": self.points}, indices=indices)
        batch.draw(shader)

    def draw_rotate_widget(self):
        gpu.state.point_size_set(self.rotate_px)
        draw_circle_2d(self.points, self.color_hover, radius=15, segments=32)

    def draw_scale_corner_widget(self):
        gpu.state.point_size_set(self.corner_px)
        shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(shader, 'POINTS', {"pos": self.points})
        batch.draw(shader)

    def draw_scale_edge_widget(self):
        gpu.state.point_size_set(self.edge_px)
        shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(shader, 'POINTS', {"pos": self.edge_points})
        batch.draw(shader)

    def draw_debug(self, points: list[Union[Vector, Sequence]]):
        shader.uniform_float("color", self.debug_color)
        batch = batch_for_shader(shader, 'POINTS', {"pos": points})
        batch.draw(shader)
