import bpy
import numpy as np
from mathutils import Vector
from typing import Literal, Optional, Union, Sequence, ClassVar
from contextlib import contextmanager
from dataclasses import dataclass
from math import radians

SCALE: int = 2  # 2 unit in 2d space is 1 unit in the 2d space
GP_DATA_NAME: str = 'GP_ANNOTATE'


def loc3d_2_r2d(location: Union[Vector, Sequence]) -> Vector:
    """Convert 3D space point to 2D space."""
    return Vector((location[0] / SCALE, location[1] / SCALE))


def r2d_2_loc3d(location: Union[Vector, Sequence]) -> Vector:
    """Convert 2D space point to 3D space."""
    return Vector((location[0] * SCALE, location[1] * SCALE, 0))


def np_vertices_from_stroke(stroke: bpy.types.GPencilStroke) -> np.ndarray:
    """Get the vertices from the stroke."""
    vertices = np.empty(len(stroke.points) * 3, dtype='f')
    stroke.points.foreach_get('co', vertices)
    return vertices.reshape((len(stroke.points), 3))


@dataclass
class GreasePencilBBox:
    """
    Calculate the bounding box of the grease pencil annotation.
    """
    gp_data: bpy.types.GreasePencil
    indices: ClassVar = ((0, 1, 2), (2, 1, 3))  # The indices of the bounding box points, use for gpu batch drawing

    max_x: float = 0
    min_x: float = 0
    max_y: float = 0
    min_y: float = 0

    @property
    def size(self) -> tuple[float, float]:
        """Return the size of the bounding box."""
        self._handle_error()
        return self.max_x - self.min_x, self.max_y - self.min_y

    @property
    def center(self) -> tuple[float, float]:
        """Return the center of the bounding box."""
        self._handle_error()
        return (self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2

    @property
    def size_2d(self) -> tuple[float, float]:
        """Return the size of the bounding box in 2d space."""
        size = self.size
        return size[0] / SCALE, size[1] / SCALE

    @property
    def center_2d(self) -> tuple[float, float]:
        """Return the center of the bounding box in 2d space."""
        center = self.center
        return center[0] / SCALE, center[1] / SCALE

    @property
    def bbox_points(self) -> tuple[tuple[float, float], ...]:
        """Return the bounding box points."""
        self._handle_error()
        return (self.min_x, self.max_y), (self.max_x, self.max_y), (self.min_x, self.min_y), (self.max_x, self.min_y)

    @property
    def bbox_points_2d(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the bounding box points in 2d space."""
        return tuple(map(loc3d_2_r2d, self.bbox_points))

    def _handle_error(self):
        if not hasattr(self, 'max_x'):
            raise ValueError('Please call calc_bbox() first.')

    @staticmethod
    def _calc_stroke_bbox(stroke: bpy.types.GPencilStroke) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate the bounding box of a stroke.
        :param stroke:
        :return:
        """
        vertices = np_vertices_from_stroke(stroke)
        max_xyz_id = np.argmax(vertices, axis=0)
        min_xyz_id = np.argmin(vertices, axis=0)

        return vertices, max_xyz_id, min_xyz_id

    @staticmethod
    def _calc_max_min(vertices: np.ndarray) -> tuple[float, float, float, float]:
        """
        Calculate the max and min of the vertices.
        :param vertices:
        :return:
        """
        max_xyz_id = np.argmax(vertices, axis=0)
        min_xyz_id = np.argmin(vertices, axis=0)

        max_x = float(vertices[max_xyz_id[0], 0])
        max_y = float(vertices[max_xyz_id[1], 1])
        min_x = float(vertices[min_xyz_id[0], 0])
        min_y = float(vertices[min_xyz_id[1], 1])

        return max_x, min_x, max_y, min_y

    def calc_bbox(self, layer_name: str, frame: int = 0) -> tuple[tuple[float, float], ...]:
        """
        Calculate the bounding box of the grease pencil annotation.
        :param layer_name: calc this layer
        :param frame: calc this frame
        :return: The bounding box of the grease pencil annotation.
            return in position of 2d space
            positions = (
                (-1, 1), (1, 1),
                (-1, -1), (1, -1))

            indices = ((0, 1, 2), (2, 1, 3))
        """

        layer = self.gp_data.layers.get(layer_name, None)
        if not layer:
            raise ValueError(f'Layer {layer_name} not found.')

        frame = layer.frames[frame]
        if not frame:
            raise ValueError(f'Frame {frame} not found.')

        x_list = []
        y_list = []
        for stroke in frame.strokes:
            max_x, min_x, max_y, min_y = self._calc_max_min(stroke)
            x_list.extend([max_x, min_x])
            y_list.extend([max_y, min_y])

        self.max_x = max(x_list)
        self.min_x = min(x_list)
        self.max_y = max(y_list)
        self.min_y = min(y_list)

        return (self.min_x, self.max_y), (self.max_x, self.max_y), (self.min_x, self.min_y), (self.max_x, self.min_y)


class GPD_Creator:
    """Grease Pencil Data Factory"""

    @classmethod
    def convert_2_gp(cls):
        bpy.ops.object.convert(target='GPENCIL', seams=False, faces=False, offset=0.01)

    @staticmethod
    def from_text(text: str, size: int = 100) -> bpy.types.GreasePencil:
        """
        Create a text object in the scene.
        :param text:  the text to display
        :param size:  in pixels
        :return:
        """
        bpy.ops.object.text_add()
        obj = bpy.context.object
        text_data = obj.data
        text_data.body = text
        text_data.size = size * SCALE

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        GPD_Creator.convert_2_gp()

        gp_obj = bpy.context.object
        gp_data = gp_obj.data
        bpy.data.objects.remove(obj)
        return gp_data

    @staticmethod
    def from_mesh_obj(obj: bpy.types.Object) -> bpy.types.GreasePencil:
        """
        Create a grease pencil object from a mesh object.
        :param obj:  the mesh object
        :return:
        """
        new_obj = obj.copy()
        bpy.context.collection.objects.link(new_obj)
        bpy.context.view_layer.objects.active = new_obj
        GPD_Creator.convert_2_gp()

        gp_obj = bpy.context.object
        gp_data = gp_obj.data
        bpy.data.objects.remove(gp_obj)

        return gp_data


@dataclass
class GreasePencilDataBuilder:
    """Grease Pencil Data Builder, easy to manipulate grease pencil data.
    usage:
    with GreasePencilDataBuilder(gp_data) as gp_builder:
        gp_builder.color('Layer', '#FF0000')
        .move('Layer', Vector((1, 1, 0)))
        .scale('Layer', Vector((2, 2, 1)), Vector((0, 0, 0)))
        .rotate('Layer', 90, Vector((0, 0, 0)))
    """
    gp_data: bpy.types.GreasePencil

    def __enter__(self):
        """allow to use with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """allow to use with statement"""
        pass

    @property
    def name(self) -> str:
        return self.gp_data.name

    @property
    def layers(self) -> list[str]:
        return [layer.name for layer in self.gp_data.layers]

    def color(self, layer_name: str, hex_color: str) -> 'GreasePencilDataBuilder':
        """Set the color of the grease pencil annotation layer.
        :param layer_name: The name of the layer.
        :param hex_color: The color in hex format.
        :return: instance"""
        layer = self.gp_data.layers.get(layer_name, None)
        if layer:
            layer.color = hex_color
        return self

    def link_nodegroup(self, nt: bpy.types.NodeTree, ) -> 'GreasePencilDataBuilder':
        """Link the grease pencil data to the node group. So that the grease pencil can be seen in the node editor."""
        nt.grease_pencils = self.gp_data
        return self

    def move(self, layer_name: str, v: Vector) -> 'GreasePencilDataBuilder':
        """Move the grease pencil data."""
        layer = self._get_layer(layer_name)

        with self._edit_space(layer_name):
            for frame in layer.frames:
                for stroke in frame.strokes:
                    self._move_stroke(stroke, v)

        return self

    def scale(self, layer_name: str, scale: Vector, pivot: Vector) -> 'GreasePencilDataBuilder':
        """Scale the grease pencil data."""
        layer = self._get_layer(layer_name)

        with self._edit_space(layer_name):
            for frame in layer.frames:
                for stroke in frame.strokes:
                    self._scale_stroke(stroke, scale, pivot)

        return self

    def rotate(self, layer_name: str, degree: int, pivot: Vector) -> 'GreasePencilDataBuilder':
        """Rotate the grease pencil data."""
        layer = self._get_layer(layer_name)

        with self._edit_space(layer_name):
            for frame in layer.frames:
                for stroke in frame.strokes:
                    self._rotate_stroke(stroke, degree, pivot)

        return self

    def join(self, other_gp_data: bpy.types.GreasePencil) -> 'GreasePencilDataBuilder':
        """Join the grease pencil data."""
        self_obj = bpy.data.objects.new('tmp', self.gp_data)
        tmp_obj = bpy.data.objects.new('tmp', other_gp_data)
        bpy.context.collection.objects.link(self_obj)
        bpy.context.collection.objects.link(tmp_obj)
        bpy.context.view_layer.objects.active = self_obj
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        self_obj.select_set(True)
        tmp_obj.select_set(True)
        bpy.ops.object.join()
        self.gp_data = self_obj.data
        bpy.data.objects.remove(self_obj)
        bpy.data.objects.remove(tmp_obj)
        return self

    def _get_layer(self, layer_name: str) -> bpy.types.GPencilLayer:
        """Handle the layer."""
        layer = self.gp_data.layers.get(layer_name, None)
        if not layer:
            raise ValueError(f'Layer {layer_name} not found.')
        return layer

    @contextmanager
    def _edit_space(self, layer_name: Optional[str] = None):
        """Edit the space of the grease pencil strokes."""
        self._set_space('3D', layer_name)
        yield
        self._set_space('2D', layer_name)
        self.gp_data.update_tag()

    def _set_space(self, type: Literal['2D', '3D'],
                   layer_name: Optional[str] = None) -> None:
        """Convert the space of the grease pencil strokes to 2D or 3D space.
        :param type: The space to convert to, either '2D' or '3D'.
        :param layer_name: The name of the layer to convert. If None, all layers will be converted.
        """
        singler_layer = self.gp_data.layers.get(layer_name, None) if layer_name else None
        space = '3DSPACE' if type == '3D' else '2DSPACE'

        def convert_layer(gplayer):
            for frame in gplayer.frames:
                for stroke in frame.strokes:
                    stroke.display_mode = space

        if singler_layer:
            convert_layer(singler_layer)
        else:
            for layer in self.gp_data.layers:
                convert_layer(layer)

    @staticmethod
    def _move_stroke(stroke: bpy.types.GPencilStroke, v: Vector):
        """Move the grease pencil data."""
        vertices = np_vertices_from_stroke(stroke)
        vertices += v
        stroke.points.foreach_set('co', vertices.ravel())

    @staticmethod
    def _scale_stroke(stroke: bpy.types.GPencilStroke, scale: Vector, pivot: Vector):
        """Scale the grease pencil data."""
        scale_3d = Vector((scale[0], scale[1], 1))
        pivot_3d = Vector((pivot[0], pivot[1], 0))
        vertices = np_vertices_from_stroke(stroke)

        vertices = (vertices - pivot_3d) * scale_3d + pivot_3d
        stroke.points.foreach_set('co', vertices.ravel())

    @staticmethod
    def _rotate_stroke(stroke: bpy.types.GPencilStroke, degree: int, pivot: Vector):
        """Rotate the grease pencil data."""
        pivot_3d = Vector((pivot[0], pivot[1], 0))
        vertices = np_vertices_from_stroke(stroke)
        vertices = (vertices - pivot_3d) @ np.array([[np.cos(radians(degree)), -np.sin(radians(degree)), 0],
                                                     [np.sin(radians(degree)), np.cos(radians(degree)), 0],
                                                     [0, 0, 1]]) + pivot_3d
        stroke.points.foreach_set('co', vertices.ravel())
