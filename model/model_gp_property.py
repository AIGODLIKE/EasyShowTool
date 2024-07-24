import bpy
import numpy as np
from contextlib import contextmanager
from typing import ClassVar
from dataclasses import dataclass
from mathutils import Vector
from .utils import VecTool


class GPencilStroke:

    @staticmethod
    @contextmanager
    def stroke_points(stroke: bpy.types.GPencilStroke) -> np.ndarray:
        """Get the vertices from the stroke."""
        yield GPencilStroke.get_stroke_points(stroke)

    @staticmethod
    def get_stroke_points(stroke: bpy.types.GPencilStroke) -> np.ndarray:
        """Get the vertices from the stroke."""
        points = np.empty(len(stroke.points) * 3, dtype='f')
        stroke.points.foreach_get('co', points)
        return points.reshape((len(stroke.points), 3))


@dataclass
class GreasePencilProperty:
    """Grease Pencil Property, a base class for grease pencil data get/set"""
    gp_data: bpy.types.GreasePencil

    @property
    def name(self) -> str:
        return self.gp_data.name

    def has_active_layer(self):
        return self.active_layer_index != -1

    @property
    def active_layer_name(self) -> str:
        """Return the active layer name."""
        return self.active_layer.info if self.has_active_layer() else ''

    @active_layer_name.setter
    def active_layer_name(self, name: str):
        """Set the active layer name."""
        if self.has_active_layer():
            self.active_layer.info = name

    @property
    def active_layer(self) -> bpy.types.GPencilLayer:
        """Return the active layer."""
        return self.gp_data.layers.active

    @property
    def active_layer_index(self) -> int:
        """Return the active layer index."""
        try:
            index = self.gp_data.layers.active_index
            return index
        except ReferenceError:
            return -1

    @active_layer_index.setter
    def active_layer_index(self, index: int):
        """Set the active layer index."""
        if self.is_empty():
            return
        if index < 0:
            self.gp_data.layers.active_index = len(self.gp_data.layers) - 1
        elif 0 <= index < len(self.gp_data.layers):
            self.gp_data.layers.active_index = index
        else:
            self.gp_data.layers.active_index = 0

        self._select_active_layer()

    def _select_active_layer(self):
        if self.active_layer is None: return
        for layer in self.gp_data.layers:
            layer.select = layer == self.active_layer

    def is_empty(self) -> bool:
        """Check if the grease pencil data is empty."""
        try:
            return not self.gp_data.layers
        except ReferenceError:
            return True

    @property
    def layer_names(self) -> list[str]:
        return [layer.info for layer in self.gp_data.layers]

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


class GPencilBBoxProperty:
    """Properties for the bounding box to use
    v2d: view 2d space e.g. in node editor, `node.location` is in v2d space
    r2d: region 2d space e.g. in the region, event.mouse_region_x is in r2d space
    """
    max_x: float = 0
    min_x: float = 0
    max_y: float = 0
    min_y: float = 0
    center: Vector = Vector((0, 0, 0))  # 3d
    # The indices of the bounding box points, use for gpu batch drawing
    indices: ClassVar = ((0, 1, 2), (2, 1, 3))

    @property
    def center_v2d(self) -> Vector:
        return VecTool.loc3d_2_v2d(self.center)

    @property
    def center_r2d(self) -> Vector:
        return VecTool.v2d_2_r2d(self.center_v2d)

    @property
    def size(self) -> Vector:
        return Vector((self.max_x - self.min_x, self.max_y - self.min_y))

    @property
    def size_v2d(self) -> Vector:
        return VecTool.loc3d_2_v2d(self.size)

    @property
    def top_left(self) -> Vector:
        return Vector((self.min_x, self.max_y))

    @property
    def top_right(self) -> Vector:
        return Vector((self.max_x, self.max_y))

    @property
    def bottom_left(self) -> Vector:
        return Vector((self.min_x, self.min_y))

    @property
    def bottom_right(self) -> Vector:
        return Vector((self.max_x, self.min_y))

    @property
    def bbox_points_3d(self) -> tuple[Vector, Vector, Vector, Vector]:
        """Return the bounding box points.
        top_left, top_right, bottom_left, bottom_right"""
        return Vector(self.top_left), Vector(self.top_right), Vector(self.bottom_left), Vector(self.bottom_right)

    @property
    def bbox_points_v2d(self) -> tuple[Vector, ...]:
        return tuple(map(VecTool.loc3d_2_v2d, self.bbox_points_3d))

    @property
    def bbox_points_r2d(self) -> tuple[Vector, ...]:
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
    def edge_center_points_v2d(self) -> tuple[Vector, ...]:
        """Return the edge center points of the bounding box in node editor view."""
        return tuple(map(VecTool.loc3d_2_v2d, self.edge_center_points_3d))

    @property
    def edge_center_points_r2d(self) -> tuple[Vector, ...]:
        """Return the edge center points of the bounding box in region 2d space."""
        return tuple(map(VecTool.v2d_2_r2d, self.edge_center_points_v2d))

    def corner_extrude_points_r2d(self, extrude: int = 15) -> list[Vector]:
        """Return the corner extrude points of the bounding box.
        :param extrude: the extrude distance
        this is not a property because it needs an extrude distance"""
        points = self.bbox_points_r2d
        # point to center vector
        vecs = [point - self.center_r2d for point in points]
        # normalize and scale
        extrude_vecs = [vec.normalized() * extrude for vec in vecs]
        new_points = [Vector(point) + vec for point, vec in zip(points, extrude_vecs)]

        return new_points
