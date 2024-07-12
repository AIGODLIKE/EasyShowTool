import bpy
import numpy as np
from mathutils import Vector, Euler
from typing import  Union, Literal
from dataclasses import dataclass, field

from .model_gp_property import GPencilStroke, GreasePencilProperty, GPencilBBoxProperty


@dataclass
class GPencilLayerBBox(GreasePencilProperty, GPencilBBoxProperty):
    """Bounding Box local to the grease pencil data.
"""
    layer: bpy.types.GPencilLayer = None
    mode: Literal['GLOBAL', 'LOCAL'] = 'GLOBAL'

    @property
    def is_local(self) -> bool:
        return self.mode == 'LOCAL'

    def to_local(self) -> 'GPencilLayerBBox':
        self.mode = 'LOCAL'
        self.calc_active_layer_bbox()
        return self

    def to_global(self) -> 'GPencilLayerBBox':
        self.mode = 'GLOBAL'
        self.calc_active_layer_bbox()
        return self

    def rotation_2d(self) -> float:
        """Return the rotation of the layer.
        notice that the rotation is stored in the layer.rotation, but the value is the inverse of the actual rotation
        see EditGreasePencilLayer in model_gp_edit.py for storing the rotation
        """
        return self.layer.rotation[2] if self.layer else 0

    def rotation_2d_inverse(self) -> float:
        return -self.layer.rotation[2] if self.layer else 0

    @property
    def bbox_points_3d(self) -> list[Vector, Vector, Vector, Vector]:
        """Return the bounding box points in 3d space.
        if the mode is local, the origin  bounding box points is correct by the inverse rotation of the layer.
        so it will apply the rotation of the layer to the bounding box points."""
        if not self.is_local:
            return super().bbox_points_3d
        points = super().bbox_points_3d
        angle = self.rotation_2d()
        pivot_3d = self.center.to_3d()
        points_3d = [p.to_3d() for p in points]
        return [((p - pivot_3d) @ Euler((0, 0, angle), 'XYZ').to_matrix() + pivot_3d).to_2d() for p in points_3d]

    @property
    def edge_center_points_3d(self) -> list[Vector, Vector, Vector, Vector]:
        """Return the edge center points of the bounding box in 3d space."""
        if not self.is_local:
            return super().edge_center_points_3d
        points = super().edge_center_points_3d
        angle = self.rotation_2d()
        pivot_3d = self.center.to_3d()
        points_3d = [p.to_3d() for p in points]
        return [((p - pivot_3d) @ Euler((0, 0, angle), 'XYZ').to_matrix() + pivot_3d).to_2d() for p in points_3d]

    def calc_active_layer_bbox(self) -> None:
        layer = self.active_layer
        if not layer:
            raise ValueError('Active layer not found.')

        self.calc_bbox(layer.info, angle=self.rotation_2d_inverse() if self.is_local else 0)

    def calc_bbox(self, layer_name_or_index: Union[str, int], angle=0) -> None:
        """
        Calculate the bounding box of the grease pencil annotation.
        :param layer_name_or_index: The name or index of the layer.
        :param angle: The rotation angle of the bounding box. which is the inverse of the layer rotation to get the correct bounding box.
        """
        layer = self._get_layer(layer_name_or_index)
        if not layer:
            raise ValueError(f'Layer {layer_name_or_index} not found.')
        self.layer = layer

        try:
            frame = layer.frames[0]
        except IndexError:  # no frame
            self.max_x = self.min_x = self.max_y = self.min_y = 0
            return

        points = self._getLayer_frame_points(frame)
        pivot = np.mean(points, axis=0)
        if angle:  # if 0, no need to rotate
            points = ((points - pivot) @ np.array([[np.cos(angle), -np.sin(angle), 0],
                                                   [np.sin(angle), np.cos(angle), 0],
                                                   [0, 0, 1]]) + pivot)

        max_xyz_id = np.argmax(points, axis=0)
        min_xyz_id = np.argmin(points, axis=0)

        max_x = float(points[max_xyz_id[0], 0])
        max_y = float(points[max_xyz_id[1], 1])
        min_x = float(points[min_xyz_id[0], 0])
        min_y = float(points[min_xyz_id[1], 1])

        self.max_x = max_x
        self.min_x = min_x
        self.max_y = max_y
        self.min_y = min_y
        self.center = Vector(pivot)
        self.last_layer_index = [i for i, l in enumerate(self.gp_data.layers) if l == layer][0]

    def _getLayer_frame_points(self, frame: bpy.types.GPencilFrame) -> np.ndarray:
        """
        Return the points of all the strokes in one numpy array.
        """

        all_points = []
        for stroke in frame.strokes:
            with GPencilStroke.stroke_points(stroke) as points:
                all_points.append(points)
        # if empty
        if not all_points:
            return np.array([[0, 0]])
        return np.concatenate(all_points, axis=0)
