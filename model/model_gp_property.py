import bpy
import numpy as np
from contextlib import contextmanager
from dataclasses import dataclass


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



