import bpy
import numpy as np
from mathutils import Vector, Euler
from typing import Union, Literal, Sequence, Callable
from dataclasses import dataclass, field

from .model_gp_property import GPencilStroke
from .model_points import PointsArea, AreaPoint
from .utils import EulerTool, VecTool


@dataclass
class CalcBBox:
    """Properties for the bounding box to use
    v2d: view 2d space e.g. in node editor, `node.location` is in v2d space
    r2d: region 2d space e.g. in the region, event.mouse_region_x is in r2d space
    """

    gp_data: bpy.types.GreasePencil
    area: PointsArea = field(init=False)
    last_layer_index: int = 0

    def __post_init__(self):
        self.area = PointsArea()

    def __getattr__(self, item: str):
        """Get the attribute from the area if it exists, otherwise from self."""
        if 'area' in self.__dict__ and hasattr(self.area, item):
            return getattr(self.area, item)
        return object.__getattribute__(self, item)

    @property
    def center_v2d(self) -> Vector:
        return VecTool.loc3d_2_v2d(self.area.center)

    @property
    def center_r2d(self) -> Vector:
        return VecTool.v2d_2_r2d(self.center_v2d)

    @property
    def size_v2d(self) -> Vector:
        return VecTool.loc3d_2_v2d(self.area.size)

    @property
    def bbox_points_3d(self) -> tuple[AreaPoint, AreaPoint, AreaPoint, AreaPoint]:
        """Return the bounding box points.
        top_left, top_right, bottom_left, bottom_right"""
        return self.area.corner_points

    @property
    def bbox_points_v2d(self) -> list[AreaPoint]:
        return [point.loc3d_2_v2d() for point in self.bbox_points_3d]

    @property
    def bbox_points_r2d(self) -> list[AreaPoint]:
        return [point.v2d_2_r2d() for point in self.bbox_points_v2d]

    @property
    def edge_center_points_3d(self) -> tuple[AreaPoint, AreaPoint, AreaPoint, AreaPoint]:
        """Return the edge center points of the bounding box."""
        return self.area.edge_center_points

    @property
    def edge_center_points_v2d(self) -> list[AreaPoint]:
        """Return the edge center points of the bounding box in node editor view."""
        return [point.loc3d_2_v2d() for point in self.edge_center_points_3d]

    @property
    def edge_center_points_r2d(self) -> list[AreaPoint]:
        """Return the edge center points of the bounding box in region 2d space."""
        return [point.v2d_2_r2d() for point in self.edge_center_points_v2d]

    def corner_extrude_points_r2d(self, extrude: int = 15) -> list[AreaPoint]:
        """Return the corner extrude points of the bounding box.
        :param extrude: the extrude distance
        this is not a property because it needs an extrude distance"""
        points = self.bbox_points_r2d
        # point to center vector
        vecs = [point - self.center_r2d for point in points]
        # normalize and scale
        extrude_vecs = [vec.normalized() * extrude for vec in vecs]
        new_points = [point + vec for point, vec in zip(points, extrude_vecs)]

        return new_points

    def calc_bbox(self, layer_name_or_index: str | int, local: bool = True) -> None:
        """
        Calculate the bounding box of the grease pencil annotation.
        :param layer_name_or_index: The name or index of the layer.
        :param local: Whether to calculate the bounding box in local or global coordinates.
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
        # Ensure all points are 3D by padding 2D points with a zero z-coordinate
        if points.shape[1] == 2:  # Check if points are 2D
            points = np.hstack([points, np.zeros((points.shape[0], 1))])  # Convert to 3D

        pivot = np.mean(points, axis=0)
        if local:
            # Adjust the points array for rotation

            if angle := -layer.rotation[2]:  # if angle is not 0
                rotation_matrix = np.array([[np.cos(angle), -np.sin(angle), 0],
                                            [np.sin(angle), np.cos(angle), 0],
                                            [0, 0, 1]])
                points = ((points - pivot) @ rotation_matrix) + pivot

        max_xyz_id = np.argmax(points, axis=0)
        min_xyz_id = np.argmin(points, axis=0)

        self.max_x = float(points[max_xyz_id[0], 0])
        self.max_y = float(points[max_xyz_id[1], 1])
        self.min_x = float(points[min_xyz_id[0], 0])
        self.min_y = float(points[min_xyz_id[1], 1])
        self.area.center = Vector(pivot)

        self.last_layer_index = [i for i, l in enumerate(self.gp_data.layers) if l == layer][0]
        self.area.setup(top=self.max_y, bottom=self.min_y, left=self.min_x, right=self.max_x)

    def _get_layer(self, layer_name_or_index: int | str) -> bpy.types.GPencilLayer:
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
class GPencilLayerBBox(CalcBBox):
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

    def layer_rotate_2d(self) -> float:
        """Return the rotation of the layer.
        notice that the rotation is stored in the layer.rotation, but the value is the inverse of the actual rotation
        see EditGreasePencilLayer in model_gp_edit.py for storing the rotation
        """
        return self.layer.rotation[2] if self.layer else 0

    def layer_rotate_2d_inverse(self) -> float:
        return -self.layer.rotation[2] if self.layer else 0

    @property
    def bbox_points_3d(self) -> Sequence[Vector]:
        """Return the bounding box points in 3d space.
        if the mode is local, the origin  bounding box points is correct by the inverse rotation of the layer.
        so it will apply the rotation of the layer to the bounding box points."""
        points = super().bbox_points_3d
        if self.is_local:
            angle = self.layer_rotate_2d()
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
            angle = self.layer_rotate_2d()
            pivot_3d = self.center.to_3d()
            points_3d = [p.to_3d() for p in points]
            return EulerTool.rotate_points(points_3d, angle, pivot_3d)
        else:
            return points

    def calc_active_layer_bbox(self) -> None:
        layer = self.gp_data.layers.active
        if not layer:
            raise ValueError('Active layer not found.')

        self.calc_bbox(layer.info, local=self.is_local)


@dataclass
class GPencilLayersBBox(CalcBBox):
    def calc_multiple_layers_bbox(self, layers: list[str | int]) -> None:
        """
        Calculate the bounding box that encompasses multiple layers.
        :param layers: A list of layer names or indices.
        """
        all_points = []
        for layer in layers:
            self.calc_bbox(layer)
            layer_points = self._getLayer_frame_points(self._get_layer(layer).frames[0])
            if layer_points.size > 0:
                # Ensure all points are 3D by padding 2D points with a zero z-coordinate
                if layer_points.shape[1] == 2:  # Check if points are 2D
                    layer_points = np.hstack([layer_points, np.zeros((layer_points.shape[0], 1))])  # Convert to 3D
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
