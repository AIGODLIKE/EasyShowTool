import gpu
import gpu.state
import gpu.shader
import bpy
import blf
from mathutils import Color, Vector
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
from typing import Sequence, Union, ClassVar

from .model_gp_bbox import GreasePencilLayerBBox
from ..public_path import get_pref

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices

from dataclasses import dataclass, field


@dataclass
class DrawModel:
    # data
    points: list[Vector, Vector, Vector, Vector]
    edge_points: list[Vector, Vector, Vector, Vector]
    coords: list[Vector, Vector, Vector, Vector, Vector]  # close the loop, for drawing lines

    # pref
    line_width: int = field(init=False)
    debug: bool = field(init=False)
    drag: bool = field(init=False)
    drag_area: bool = field(init=False)
    # color
    color: Color = field(init=False)
    color_hover: Color = field(init=False)
    color_area: Color = field(init=False)
    # detect
    corner_px: int = field(init=False)
    edge_px: int = field(init=False)
    rotate_px: int = field(init=False)

    # default
    debug_color: Color = field(init=False)
    point_size: ClassVar[int] = 20

    def __post_init__(self):
        theme = bpy.context.preferences.themes['Default'].view_3d
        self.line_width = get_pref().gp_draw_line_width
        self.debug = get_pref().debug_draw
        self.drag = get_pref().gp_draw_drag
        self.drag_area = get_pref().gp_draw_drag_area

        scale_factor = 0.75  # scale factor for the points, make it smaller
        self.corner_px = get_pref().gp_detect_corner_px * scale_factor
        self.edge_px = get_pref().gp_detect_edge_px * scale_factor
        self.rotate_px = get_pref().gp_detect_rotate_px * scale_factor

        self.color = self.color_alpha(theme.lastsel_point, 0.3)
        self.color_highlight = self.color_alpha(theme.lastsel_point, 0.8)
        self.color_hover = self.color_alpha(theme.vertex_select, 0.8)
        self.color_area = self.color_alpha(theme.face, 0.5)
        self.debug_color = self.color_alpha(theme.face_back, 0.8)

        gpu.state.line_width_set(self.line_width)
        gpu.state.point_size_set(self.point_size)
        gpu.state.blend_set('ALPHA')

    @staticmethod
    def color_alpha(color: Color, alpha: float) -> tuple:
        return color[0], color[1], color[2], alpha

    def draw_bbox_points(self):
        shader.uniform_float("color", self.color_highlight)
        batch = batch_for_shader(shader, 'POINTS', {"pos": self.points})
        batch.draw(shader)

    def draw_bbox_edge(self, highlight: bool = False):
        gpu.state.point_size_set(10)
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": self.coords})
        shader.uniform_float("color", self.color if not highlight else self.color_highlight)
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

    def _draw_text(self, text_lines: Sequence[str], size=24, space: int = 5):
        font_id = 0
        shader.uniform_float("color", self.color)
        # start from the bottom left corner
        x, y = 20, 20
        # draw some text
        for i, line in enumerate(text_lines):
            if i % 2 == 0:
                blf.color(font_id, 0.5, 0.5, 0.5, 1)
            else:
                blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x, y + i * size + space, 0)
            blf.size(font_id, size)
            blf.draw(font_id, line)

    def draw_debug(self, dict_info: dict[str, str]):
        shader.uniform_float("color", self.debug_color)
        textlines = []


        for k, v in dict_info.items():
            k_str = k.ljust(30, "-")
            textlines.append(f"{k_str}:{v}")

        if textlines:
            self._draw_text(textlines)
