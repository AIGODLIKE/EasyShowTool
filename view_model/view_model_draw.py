from dataclasses import dataclass, field
from mathutils import Vector, Color
from typing import Sequence, OrderedDict
import numpy as np
import gpu
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
import blf

from ..model.model_draw import DrawData, DrawPreference
from ..model.model_gp_bbox import GreasePencilLayerBBox

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices


@dataclass
class DrawViewModel:
    draw_data: DrawData
    draw_preference: DrawPreference

    def __getattr__(self, item):
        """Get the attribute from the draw data or draw preference."""
        if hasattr(self.pref, item):
            return getattr(self.pref, item)
        elif hasattr(self.draw_data, item):
            return getattr(self.draw_data, item)

    def update_draw_data(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.draw_data.__annotations__:
                setattr(self.draw_data, key, value)

    def __post_init__(self):
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

    def draw_shapes(self, point: np.ndarray):
        shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(shader, 'POINTS', {"pos": point})
        batch.draw(shader)

    def draw_line(self, start_pos, end_pos):
        shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(shader, 'LINES', {"pos": [start_pos, end_pos]})
        batch.draw(shader)

    def _draw_text_left_bottom(self, text_lines: Sequence[str], size=24, space: int = 5):
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

    def draw_text(self, text: str, pos: Vector, size=24):
        font_id = 0
        shader.uniform_float("color", self.color)
        blf.color(font_id, 1, 1, 1, 1)
        blf.position(font_id, pos.x, pos.y, 0)
        blf.size(font_id, size)
        blf.draw(font_id, text)

    def draw_debug_info(self, dict_info: OrderedDict[str, str]):
        shader.uniform_float("color", self.debug_color)
        textlines = []

        for k, v in dict_info.items():
            k_str = k.ljust(30, "-")
            textlines.append(f"{k_str}:{v}")

        if textlines:
            self._draw_text_left_bottom(textlines)

        if not self.start_pos or not self.end_pos: return
        if self.end_pos[0] == 0 and self.end_pos[1] == 0: return
        if self.start_pos[0] == 0 and self.start_pos[1] == 0: return
        self.draw_line(self.start_pos, self.end_pos)
        dis = round((self.start_pos - self.end_pos).length, 2)
        middle = (self.start_pos + self.end_pos) / 2
        self.draw_text(f"{dis}px", middle)

        if self.delta_degree:
            center = (self.points[0] + self.points[2]) / 2
            self.draw_line(center, self.end_pos)
            self.draw_line(center, self.start_pos)
            self.draw_text(f"{self.delta_degree}°", self.end_pos + Vector((0, 20)))
            draw_circle_2d(self.start_pos, self.color_hover, radius=dis, segments=128)
