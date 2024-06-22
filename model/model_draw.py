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

from .utils import VecTool
from .model_gp_bbox import GreasePencilLayerBBox
from ..public_path import get_pref

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices


class DrawShape:
    shapes: ClassVar[dict] = {}

    def load_obj(self, blend_path: Path, obj_name='gz_shape_ROTATE'):
        if obj_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[obj_name])
        with bpy.data.libraries.load(str(blend_path)) as (data_from, data_to):
            data_to.objects = [obj_name]
        self.shapes[obj_name] = data_to.objects[0]
        return self.shapes[obj_name]

    @staticmethod
    def draw_points_from_obj(obj: bpy.types.Object, draw_type: Literal['TRIS', 'LINES'],
                             size: int = 100) -> np.ndarray:
        """get the draw points from the object, return the vertices of the object"""
        tmp_mesh: bpy.types.Mesh = obj.data

        mesh = tmp_mesh
        vertices = np.zeros((len(mesh.vertices), 3), 'f')
        mesh.vertices.foreach_get("co", vertices.ravel())
        mesh.calc_loop_triangles()

        if draw_type == 'LINES':
            edges = np.zeros((len(mesh.edges), 2), 'i')
            mesh.edges.foreach_get("vertices", edges.ravel())
            custom_shape_verts = vertices[edges].reshape(-1, 3)
        else:
            tris = np.zeros((len(mesh.loop_triangles), 3), 'i')
            mesh.loop_triangles.foreach_get("vertices", tris.ravel())
            custom_shape_verts = vertices[tris].reshape(-1, 3)

        custom_shape_verts *= size

        return custom_shape_verts


@dataclass
class DrawModel:
    # data
    points: list[Vector, Vector, Vector, Vector]
    edge_points: list[Vector, Vector, Vector, Vector]
    coords: list[Vector, Vector, Vector, Vector, Vector]  # close the loop, for drawing lines
    start_pos: Optional[Vector] = None
    end_pos: Optional[Vector] = None
    delta_degree: Optional[float] = None

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
