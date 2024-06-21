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
    points: list[Vector, Vector, Vector, Vector]
    edge_points: list[Vector, Vector, Vector, Vector]
    coords: list[Vector, Vector, Vector, Vector, Vector]  # close the loop, for drawing lines

    # pref
    line_width: int = field(init=False)
    debug: bool = field(init=False)
    drag: bool = field(init=False)
    drag_area: bool = field(init=False)
    color: Color = field(init=False)
    color_hover: Color = field(init=False)
    color_area: Color = field(init=False)
    # detect
    corner_px: int = field(init=False)
    edge_px: int = field(init=False)
    rotate_px: int = field(init=False)

    # default
    debug_color: tuple = (1, 0, 0, 1)
    point_size: ClassVar[int] = 20

    def __post_init__(self):
        self.line_width = get_pref().gp_draw_line_width
        self.debug = get_pref().debug_draw
        self.drag = get_pref().gp_draw_drag
        self.drag_area = get_pref().gp_draw_drag_area
        self.color = get_pref().gp_color
        self.color_hover = get_pref().gp_color_hover
        self.color_area = get_pref().gp_color_area
        self.corner_px = get_pref().gp_detect_corner_px
        self.edge_px = get_pref().gp_detect_edge_px
        self.rotate_px = get_pref().gp_detect_rotate_px

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

    def draw_rotate_widget(self, point: Vector):
        gpu.state.point_size_set(self.rotate_px)
        draw_circle_2d(point, self.color_hover, radius=15, segments=32)

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
