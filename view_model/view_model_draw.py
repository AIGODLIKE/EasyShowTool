from dataclasses import dataclass, field
from mathutils import Vector, Color
from typing import Sequence, OrderedDict
import numpy as np
import gpu
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d
import blf

from ..model.model_draw import DrawData, DrawPreference
from ..model.model_gp_bbox import GPencilLayerBBox
from ..model.model_points import PointsArea

indices = PointsArea.indices


@dataclass
class DrawViewModel:
    draw_data: DrawData
    draw_preference: DrawPreference

    shader: gpu.types.GPUShader = field(init=False)

    def __getattr__(self, item):
        """Get the attribute from the draw data or draw preference."""
        if hasattr(self.draw_preference, item):
            return getattr(self.draw_preference, item)
        elif hasattr(self.draw_data, item):
            return getattr(self.draw_data, item)

    def update_draw_data(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.draw_data.__annotations__:
                setattr(self.draw_data, key, value)

    def __post_init__(self):
        self.shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        gpu.state.line_width_set(self.line_width)
        gpu.state.point_size_set(self.point_size)
        gpu.state.blend_set('ALPHA')

    @staticmethod
    def color_alpha(color: Color, alpha: float) -> tuple:
        return color[0], color[1], color[2], alpha

    def draw_bbox_points(self):
        self.shader.uniform_float("color", self.color_highlight)
        batch = batch_for_shader(self.shader, 'POINTS', {"pos": self.points})
        batch.draw(self.shader)

    def draw_bbox_edge(self, highlight: bool = False):
        gpu.state.point_size_set(10)
        batch = batch_for_shader(self.shader, 'LINE_STRIP', {"pos": self.coords})
        self.shader.uniform_float("color", self.color if not highlight else self.color_highlight)
        batch.draw(self.shader)

    def draw_bbox_area(self):
        gpu.state.blend_set('ALPHA')
        self.shader.uniform_float("color", self.color_area)
        batch = batch_for_shader(self.shader, 'TRIS', {"pos": self.points}, indices=indices)
        batch.draw(self.shader)

    def draw_rotate_widget(self, point: Vector):
        gpu.state.point_size_set(self.rotate_px)
        draw_circle_2d(point, self.color_hover, radius=15, segments=32)

    def draw_scale_corner_widget(self):
        gpu.state.point_size_set(self.corner_px)
        self.shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(self.shader, 'POINTS', {"pos": self.points})
        batch.draw(self.shader)

    def draw_scale_edge_widget(self):
        gpu.state.point_size_set(self.edge_px)
        self.shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(self.shader, 'POINTS', {"pos": self.edge_points})
        batch.draw(self.shader)

    def draw_shapes(self, point: np.ndarray):
        self.shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(self.shader, 'POINTS', {"pos": point})
        batch.draw(self.shader)

    def draw_line(self, start_pos, end_pos):
        self.shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(self.shader, 'LINES', {"pos": [start_pos, end_pos]})
        batch.draw(self.shader)

    def draw_box_outline(self, points: Sequence[Vector], color: Color | list = None):
        if color:
            self.shader.uniform_float("color", color)
        else:
            self.shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(self.shader, 'LINE_LOOP', {"pos": points})
        batch.draw(self.shader)

    def draw_box_area(self, points: Sequence[Vector], color: Color | list = None):
        if color:
            self.shader.uniform_float("color", color)
        else:
            self.shader.uniform_float("color", self.color_hover)
        batch = batch_for_shader(self.shader, 'TRIS', {"pos": points}, indices=indices)
        batch.draw(self.shader)

    def _draw_text_left_bottom(self, text_lines: Sequence[str], size=24, space: int = 5):
        font_id = 0
        self.shader.uniform_float("color", self.color)
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
        self.shader.uniform_float("color", self.color)
        blf.color(font_id, 1, 1, 1, 1)
        blf.position(font_id, pos.x, pos.y, 0)
        blf.size(font_id, size)
        blf.draw(font_id, text)

    def draw_rotate_angle(self):
        if self.delta_degree:
            self.draw_text(f"{round(self.delta_degree, 1)}°", Vector((self.mouse_state.end_pos)) + Vector((0, 20)))

    def draw_select_box(self):
        if not self.mouse_state: return
        if not self.mouse_state.is_move: return
        # draw a selected box with the start and end pos
        if not self.mouse_state.start_pos.x > 0: return

        gpu.state.blend_set('ALPHA')
        select_color = list(self.color_highlight)
        select_color[3] = 0.5
        area: PointsArea = self.mouse_state.drag_area()
        points = area.corner_points_line_order
        self.draw_box_outline(points, color=select_color)
        # draw area
        select_color[3] = 0.025
        points = area.corner_points
        self.draw_box_area(points, color=select_color)
        # draw the line between start and end pos
        # self.draw_line(self.mouse_state.start_pos, self.mouse_state.end_pos)
        # draw the distance between start and end pos

    def draw_debug_info(self, dict_info: OrderedDict[str, str]):
        self.shader.uniform_float("color", self.debug_color)
        textlines = []

        for k, v in dict_info.items():
            k_str = k.ljust(30, "-")
            textlines.append(f"{k_str}:{v}")

        if textlines:
            self._draw_text_left_bottom(textlines)

        if not self.mouse_state: return
        if not self.mouse_state.is_move: return
        dis = round((self.mouse_state.start_pos - self.mouse_state.end_pos).length, 2)
        self.draw_text(f"{dis}px", self.mouse_state.end_pos + Vector((+20, -20)))
