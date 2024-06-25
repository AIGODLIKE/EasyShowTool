from dataclasses import dataclass, field
from mathutils import Vector, Color
import bpy
from typing import Optional, ClassVar, Literal
from pathlib import Path
import bmesh
import numpy as np

from ..public_path import get_pref


@dataclass(slots=True)
class DrawPreference:
    """blender draw preference for grease pencil, collect all the draw preference here"""
    # lazy update
    lazy_update: bool = field(init=False)
    # pref
    line_width: int = field(init=False)
    debug: bool = field(init=False)
    drag: bool = field(init=False)
    drag_area: bool = field(init=False)
    # color
    color: Color = field(init=False)
    color_hover: Color = field(init=False)
    color_highlight: Color = field(init=False)
    color_area: Color = field(init=False)
    # detect
    corner_px: int = field(init=False)
    edge_px: int = field(init=False)
    rotate_px: int = field(init=False)
    # default
    debug_color: Color = field(init=False)
    point_size: ClassVar[int] = 20

    @staticmethod
    def color_alpha(color: Color, alpha: float) -> tuple:
        return color[0], color[1], color[2], alpha

    def __post_init__(self):
        self.lazy_update = get_pref().gp_performance.lazy_update

        theme = bpy.context.preferences.themes['Default'].view_3d
        self.line_width = get_pref().gp_draw.line_width
        self.drag = get_pref().gp_draw.drag
        self.drag_area = get_pref().gp_draw.drag_area
        self.debug = get_pref().debug

        scale_factor = 0.75  # scale factor for the points, make it smaller
        self.corner_px = get_pref().gp_performance.detect_corner_px * scale_factor
        self.edge_px = get_pref().gp_performance.detect_edge_px * scale_factor
        self.rotate_px = get_pref().gp_performance.detect_rotate_px * scale_factor

        self.color = self.color_alpha(theme.lastsel_point, 0.3)
        self.color_highlight = self.color_alpha(theme.lastsel_point, 0.8)
        self.color_hover = self.color_alpha(theme.vertex_select, 0.8)
        self.color_area = self.color_alpha(theme.face, 0.5)
        self.debug_color = self.color_alpha(theme.face_back, 0.8)


@dataclass(slots=True)
class DrawData:
    """Draw data for grease pencil, collect all the draw data need here"""
    points: list[Vector, Vector, Vector, Vector]
    edge_points: list[Vector, Vector, Vector, Vector]
    start_pos: Optional[Vector] = None
    end_pos: Optional[Vector] = None
    # from transform handles
    delta_degree: Optional[float] = None
    delta_scale: Optional[Vector] = None
    delta_move: Optional[Vector] = None

    @property
    def coords(self) -> list[Vector]:
        # close the loop
        top_left, top_right, bottom_left, bottom_right = self.points
        return [top_left, top_right, bottom_right, bottom_left, top_left]


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
