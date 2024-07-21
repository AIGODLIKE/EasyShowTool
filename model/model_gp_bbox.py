import bpy
import numpy as np
from mathutils import Vector, Euler
from typing import Union, Literal, Sequence, Callable
from dataclasses import dataclass, field

from .model_gp_property import GPencilStroke, GreasePencilProperty, GPencilBBoxProperty
from .utils import EulerTool


@dataclass
class CalcBBox():
    gp_data: bpy.types.GreasePencil

    def _get_layer(self, layer_name_or_index: Union[int, str]) -> bpy.types.GPencilLayer:
        """Handle the layer.
        :param layer_name_or_index: The name or index of the layer.
        :return: The layer object.
        """
        if isinstance(layer_name_or_index, int):
            try:
                layer = self.gp_data.layers[layer_name_or_index]
            except ValueError:
                raise ValueError(f'Layer index {layer_name_or_index} not found.')
        else:
            layer = self.gp_data.layers.get(layer_name_or_index, None)
        if not layer:
            raise ValueError(f'Layer {layer_name_or_index} not found.')
        return layer

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
        # self.center = Vector(((max_x + min_x) / 2, (max_y + min_y) / 2, 0))
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


@dataclass
class GPencilLayerBBox(CalcBBox, GPencilBBoxProperty):
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
    def bbox_points_3d(self) -> Sequence[Vector]:
        """Return the bounding box points in 3d space.
        if the mode is local, the origin  bounding box points is correct by the inverse rotation of the layer.
        so it will apply the rotation of the layer to the bounding box points."""
        points = super().bbox_points_3d
        if self.is_local:
            angle = self.rotation_2d()
            pivot_3d = self.center.to_3d()
            points_3d = [p.to_3d() for p in points]
            return EulerTool.rotate_points(points_3d, angle, pivot_3d)
        else:
            return points

    @property
    def edge_center_points_3d(self) -> Sequence[Vector]:
        """Return the edge center points of the bounding box in 3d space."""
        points = super().edge_center_points_3d
        if self.is_local:
            angle = self.rotation_2d()
            pivot_3d = self.center.to_3d()
            points_3d = [p.to_3d() for p in points]
            return EulerTool.rotate_points(points_3d, angle, pivot_3d)
        else:
            return points

    def calc_active_layer_bbox(self) -> None:
        layer = self.gp_data.layers.active
        if not layer:
            raise ValueError('Active layer not found.')

        self.calc_bbox(layer.info, angle=self.rotation_2d_inverse() if self.is_local else 0)


@dataclass
class GPencilLayersBBox(CalcBBox, GPencilBBoxProperty):
    def calc_multiple_layers_bbox(self, layers: list[Union[str, int]]) -> None:
        """
        Calculate the bounding box that encompasses multiple layers.
        :param layers: A list of layer names or indices.
        """
        all_points = []
        for layer in layers:
            self.calc_bbox(layer)
            layer_points = self._getLayer_frame_points(self._get_layer(layer).frames[0])
            if layer_points.size > 0:
                all_points.append(layer_points)

        if not all_points:
            self.max_x = self.min_x = self.max_y = self.min_y = 0
            return

        all_points = np.concatenate(all_points, axis=0)
        pivot = np.mean(all_points, axis=0)

        max_xyz_id = np.argmax(all_points, axis=0)
        min_xyz_id = np.argmin(all_points, axis=0)

        self.max_x = float(all_points[max_xyz_id[0], 0])
        self.max_y = float(all_points[max_xyz_id[1], 1])
        self.min_x = float(all_points[min_xyz_id[0], 0])
        self.min_y = float(all_points[min_xyz_id[1], 1])
        self.center = Vector(pivot)
