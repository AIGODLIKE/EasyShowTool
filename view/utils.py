from pathlib import Path
from typing import ClassVar, Literal
import bpy
import numpy as np
import bmesh


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
