import bpy
import numpy as np
from mathutils import Vector, Euler
from typing import Sequence, Union, ClassVar, Optional, Literal
from dataclasses import dataclass, field

from .utils import VecTool
from .model_gp_edit import EditGreasePencilStroke
from .model_gp import GreasePencilProperty


@dataclass
class GreasePencilLayerBBox(GreasePencilProperty):
    """
    Calculate the bounding box of the grease pencil bounding box. useful for drawing the bounding box.
    """
    # The indices of the bounding box points, use for gpu batch drawing
    indices: ClassVar = ((0, 1, 2), (2, 1, 3))
    # The bounding box max and min values
    max_x: float = 0
    min_x: float = 0
    max_y: float = 0
    min_y: float = 0
    center: Vector = Vector((0, 0, 0))
    #
    layer: bpy.types.GPencilLayer = None
    last_layer_index: int = None

    @property
    def size(self) -> tuple[float, float]:
        """Return the 3d size of the bounding box."""
        return self.max_x - self.min_x, self.max_y - self.min_y

    def rotation_2d(self) -> float:
        """Return the rotation of the layer.
        notice that the rotation is stored in the layer.rotation, but the value is the inverse of the actual rotation
        see EditGreasePencilLayer in model_gp_edit.py for storing the rotation
        """
        return self.layer.rotation[2] if self.layer else 0

    def rotation_2d_inverse(self) -> float:
        return -self.layer.rotation[2] if self.layer else 0

    @property
    def size_v2d(self) -> Vector:
        """Return the 2d view size of the bounding box."""
        return VecTool.loc3d_2_v2d(self.size)

    @property
    def center_v2d(self) -> Vector:
        """Return the 2d view center of the bounding box."""
        return VecTool.loc3d_2_v2d(self.center)

    @property
    def center_r2d(self) -> Vector:
        """Return the 2d region center of the bounding box."""
        return VecTool.v2d_2_r2d(self.center_v2d)

    @property
    def top_left(self) -> tuple[float, float]:
        """Return the 3d top left point of the bounding box."""
        return self.min_x, self.max_y

    @property
    def top_right(self) -> tuple[float, float]:
        """Return the 3d top right point of the bounding box."""
        return self.max_x, self.max_y

    @property
    def bottom_left(self) -> tuple[float, float]:
        """Return the 3d bottom left point of the bounding box."""
        return self.min_x, self.min_y

    @property
    def bottom_right(self) -> tuple[float, float]:
        """Return the 3d bottom right point of the bounding box."""
        return self.max_x, self.min_y

    @property
    def bbox_points_3d(self, apply_rotate: bool = True) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the bounding box points."""
        # top_left, top_right, bottom_left, bottom_right
        points = Vector(self.top_left), Vector(self.top_right), Vector(self.bottom_left), Vector(self.bottom_right)
        if apply_rotate:
            angle = self.rotation_2d()
            pivot_3d = self.center.to_3d()
            points_3d = [p.to_3d() for p in points]
            # rotate
            points_3d = [(p - pivot_3d) @ Euler((0, 0, angle), 'XYZ').to_matrix() + pivot_3d for p in points_3d]
            points = [Vector(p).to_2d() for p in points_3d]
        return points

    @property
    def bbox_points_v2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the bounding box points in node editor view."""
        return tuple(map(VecTool.loc3d_2_v2d, self.bbox_points_3d))

    @property
    def bbox_points_r2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the bounding box points in region 2d space."""

        return tuple(map(VecTool.v2d_2_r2d, self.bbox_points_v2d))

    @property
    def edge_center_points_3d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the edge center points of the bounding box."""
        top_center = (self.max_x + self.min_x) / 2, self.max_y
        bottom_center = (self.max_x + self.min_x) / 2, self.min_y
        left_center = self.min_x, (self.max_y + self.min_y) / 2
        right_center = self.max_x, (self.max_y + self.min_y) / 2
        return Vector(top_center), Vector(bottom_center), Vector(left_center), Vector(right_center)

    @property
    def edge_center_points_v2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the edge center points of the bounding box in node editor view."""
        return tuple(map(VecTool.loc3d_2_v2d, self.edge_center_points_3d))

    @property
    def edge_center_points_r2d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the edge center points of the bounding box in region 2d space."""
        return tuple(map(VecTool.v2d_2_r2d, self.edge_center_points_v2d))

    def corner_extrude_points_r2d(self, extrude: int = 10) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the corner extrude points of the bounding box.
        :param extrude: the extrude distance
        this is not a property because it needs an extrude distance"""
        points = self.bbox_points_r2d
        extrude_vecs = [Vector((-extrude, extrude)), Vector((extrude, extrude)), Vector((-extrude, -extrude)),
                        Vector((extrude, -extrude))]  # top_left, top_right, bottom_left, bottom_right
        new_points = [Vector(point) + vec for point, vec in zip(points, extrude_vecs)]

        return new_points

    @staticmethod
    def _calc_stroke_bbox(stroke: bpy.types.GPencilStroke, rotate_z: float) -> tuple[
        float, float, float, float, Vector]:
        """
        Calculate the bounding box of a stroke.
        :param stroke:
        :param rotate_z: rotate back the stroke
        :return:
        """
        with EditGreasePencilStroke.stroke_points(stroke) as points:
            pivot = np.mean(points, axis=0)
            if rotate_z:  # if 0, no need to rotate
                angle = rotate_z
                points = ((points - pivot) @ np.array([[np.cos(angle), -np.sin(angle), 0],
                                                       [np.sin(angle), np.cos(angle), 0],
                                                       [0, 0, 1]]) + pivot)
            max_xyz_id = np.argmax(points, axis=0)
            min_xyz_id = np.argmin(points, axis=0)

            max_x = float(points[max_xyz_id[0], 0])
            max_y = float(points[max_xyz_id[1], 1])
            min_x = float(points[min_xyz_id[0], 0])
            min_y = float(points[min_xyz_id[1], 1])

        return max_x, min_x, max_y, min_y, Vector(pivot)

    def _calc_layer_bbox(self, frame: bpy.types.GPencilFrame, rotate_z=float) -> None:
        """
        Calculate the bounding box of the grease pencil annotation layer.
        :param frame: calc this frame
        """
        points = self._get_layer_points(frame)
        pivot = np.mean(points, axis=0)
        if rotate_z:  # if 0, no need to rotate
            angle = rotate_z
            points = ((points - pivot) @ np.array([[np.cos(angle), -np.sin(angle), 0],
                                                   [np.sin(angle), np.cos(angle), 0],
                                                   [0, 0, 1]]) + pivot)

        max_xyz_id = np.argmax(points, axis=0)
        min_xyz_id = np.argmin(points, axis=0)

        max_x = float(points[max_xyz_id[0], 0])
        max_y = float(points[max_xyz_id[1], 1])
        min_x = float(points[min_xyz_id[0], 0])
        min_y = float(points[min_xyz_id[1], 1])

        return max_x, min_x, max_y, min_y, Vector(pivot)

    def _get_layer_points(self, frame) -> np.ndarray:
        """
        Return the points of all the strokes in one numpy array.
        """

        all_points = []
        for stroke in frame.strokes:
            with EditGreasePencilStroke.stroke_points(stroke) as points:
                all_points.append(points)

        return np.concatenate(all_points, axis=0)

    def calc_active_layer_bbox(self) -> None:
        """
        Calculate the bounding box of the active grease pencil annotation layer.
        :param frame: calc this frame
        """
        layer = self.active_layer
        if not layer:
            raise ValueError('Active layer not found.')

        return self.calc_bbox(layer.info)

    def calc_bbox(self, layer_name_or_index: Union[str, int]) -> None:
        """
        Calculate the bounding box of the grease pencil annotation.
        :param layer_name_or_index: The name or index of the layer.
        :param frame: calc this frame
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

        points = self._get_layer_points(frame)
        angle = self.rotation_2d_inverse()
        pivot = np.mean(points, axis=0)
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
        # rotate the bounding box back
        self.last_layer_index = [i for i, l in enumerate(self.gp_data.layers) if l == layer][0]
