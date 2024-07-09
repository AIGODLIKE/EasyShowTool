from contextlib import contextmanager
from math import radians
from typing import Union
import bpy
import numpy as np
from mathutils import Vector, Matrix
from typing import Literal


# below Edit Class is all in 3d space

class EditGreasePencilStroke:
    """Grease Pencil Stroke, easy to manipulate Stroke data."""

    @staticmethod
    @contextmanager
    def stroke_points(stroke: bpy.types.GPencilStroke) -> np.ndarray:
        """Get the vertices from the stroke."""
        points = np.empty(len(stroke.points) * 3, dtype='f')
        stroke.points.foreach_get('co', points)
        yield points.reshape((len(stroke.points), 3))

    def _move_stroke(self, stroke: bpy.types.GPencilStroke, v: Vector):
        """Move the grease pencil data."""
        move_3d = Vector((v[0], v[1], 0))
        with self.stroke_points(stroke) as points:
            points += move_3d
            stroke.points.foreach_set('co', points.ravel())

    def _scale_stroke(self, stroke: bpy.types.GPencilStroke, scale: Vector, pivot: Vector):
        """Scale the grease pencil data."""
        scale_3d = Vector((scale[0], scale[1], 1))
        pivot_3d = Vector((pivot[0], pivot[1], 0))
        with self.stroke_points(stroke) as points:
            points = (points - pivot_3d) * scale_3d + pivot_3d
            stroke.points.foreach_set('co', points.ravel())

    def _rotate_stroke(self, stroke: bpy.types.GPencilStroke, degree: int, pivot: Vector):
        """Rotate the grease pencil data around the pivot point."""
        pivot_3d = Vector((pivot[0], pivot[1], 0))
        angle = radians(degree)
        with self.stroke_points(stroke) as points:
            # use numpy to calculate the rotation
            points = ((points - pivot_3d) @ np.array([[np.cos(angle), -np.sin(angle), 0],
                                                      [np.sin(angle), np.cos(angle), 0],
                                                      [0, 0, 1]]) + pivot_3d)

            stroke.points.foreach_set('co', points.ravel())


class EditGreasePencilLayer(EditGreasePencilStroke):
    """Grease Pencil Layer, easy to manipulate Layer data."""

    def move_layer(self, layer: bpy.types.GPencilLayer, v: Vector):
        for frame in layer.frames:
            for stroke in frame.strokes:
                self._move_stroke(stroke, v)

    def scale_layer(self, layer: bpy.types.GPencilLayer, scale: Vector, pivot: Vector):
        for frame in layer.frames:
            for stroke in frame.strokes:
                self._scale_stroke(stroke, scale, pivot)

    def scale_local_layer(self, layer: bpy.types.GPencilLayer, scale: Vector, degree: int, pivot: Vector):
        """rotate the layer first, then scale the layer, then rotate back"""
        self.rotate_layer(layer, -degree, pivot)
        self.scale_layer(layer, scale, pivot)
        self.rotate_layer(layer, degree, pivot)

    def rotate_layer(self, layer: bpy.types.GPencilLayer, degree: int, pivot: Vector):
        for frame in layer.frames:
            for stroke in frame.strokes:
                self._rotate_stroke(stroke, degree, pivot)

        # store rotation in layer.rotation, but inverse the rotation
        # because rotate from z up view in 3d clockwise, value is negative
        # so store the inverse value, to make it always looks straight in 3d view, easy to debug
        layer.rotation[2] += radians(degree)

    def display_in_2d(self, layer: bpy.types.GPencilLayer):
        self._set_display_mode(layer, '2DSPACE')

    def display_in_3d(self, layer: bpy.types.GPencilLayer):
        self._set_display_mode(layer, '3DSPACE')

    def is_in_2d(self, layer: bpy.types.GPencilLayer) -> bool:
        return self._get_display_mode(layer) == '2DSPACE'

    @staticmethod
    def _set_display_mode(layer: bpy.types.GPencilLayer, mode: Literal['2DSPACE', '3DSPACE']):
        for frame in layer.frames:
            for stroke in frame.strokes:
                if stroke.display_mode != mode:
                    stroke.display_mode = mode

    @staticmethod
    def _get_display_mode(layer: bpy.types.GPencilLayer) -> Literal['2DSPACE', '3DSPACE']:
        if not layer.frames or not layer.frames[0].strokes:
            return '3DSPACE'
        return layer.frames[0].strokes[0].display_mode
