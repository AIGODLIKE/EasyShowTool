import bpy
import numpy as np
from mathutils import Vector
from typing import Literal, Optional, Union, Sequence, ClassVar, Final
from contextlib import contextmanager
from dataclasses import dataclass, field
from math import radians


def s_scale(v: float, r: bool = False) -> float:
    """
    this is a very strange convert grease pencil annotation location between 2d space to 3d space
    :param v: value
    :param r: reverse False: 3d -> 2d, True: 2d -> 3d
    :return: value

    SCALE: float = 1.1145124817 measure by hand
    """

    return v / 2 * 1.1145124817 if not r else v * 2 / 1.1145124817


def loc3d_2_r2d(location: Union[Vector, Sequence]) -> Vector:
    """Convert 3D space point to 2D space."""
    return Vector((s_scale(location[0]), s_scale(location[1])))


def r2d_2_loc3d(location: Union[Vector, Sequence]) -> Vector:
    """Convert 2D space point to 3D space."""
    return Vector((s_scale(location[0], r=True), s_scale(location[1], r=True)))


@dataclass
class GP_Color:

    @staticmethod
    def hex_2_rgb(hex_color: str) -> list[float, float, float]:
        """Convert hex color to rgb color."""
        if hex_color.startswith('#'):
            hex = hex_color[1:]
        else:
            hex = hex_color
        return [int(hex[i:i + 2], 16) / 255 for i in (0, 2, 4)]


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
        return s_scale(size[0]), s_scale(size[1])

    @property
    def center_2d(self) -> tuple[float, float]:
        """Return the center of the bounding box in 2d space."""
        center = self.center
        return s_scale(center[0]), s_scale(center[1])

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
        with EditGreasePencilStroke.stroke_points(stroke) as vertices:
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


class GreasePencilCache:
    """Grease Pencil Cache, cache the grease pencil objects."""
    tmp_objs: ClassVar[list[bpy.types.Object]] = []

    @classmethod
    def cleanup(cls):
        for obj in cls.tmp_objs:
            try:
                bpy.data.objects.remove(obj)
            except:
                pass
        cls.tmp_objs.clear()

    @classmethod
    def del_later(cls, obj: Optional[bpy.types.Object] = None, obj_list: Optional[list[bpy.types.Object]] = None):
        if obj:
            cls.tmp_objs.append(obj)
        if obj_list:
            cls.tmp_objs.extend(obj_list)


class CreateGreasePencilData(GreasePencilCache):
    """Grease Pencil Data Factory, a static class that makes it easy to create grease pencil data.
    :param seam:  Add seam to the grease pencil data.
    :param faces: Add faces to the grease pencil data.
    :param offset: The offset of the grease pencil data.
    """

    seam: ClassVar[bool] = False
    faces: ClassVar[bool] = False
    offset: ClassVar[float] = 0.01

    @classmethod
    def convert_2_gp(cls):
        bpy.ops.object.convert(target='GPENCIL', seams=cls.seam, faces=cls.faces, offset=cls.offset)

    @staticmethod
    def empty() -> bpy.types.GreasePencil:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.gpencil_add(type='EMPTY')
        obj = bpy.context.object
        gp_data = obj.data
        CreateGreasePencilData.del_later(obj)
        return gp_data

    @staticmethod
    def from_text(text: str, size: int = 100, hex_color: str = '#E7E7E7') -> bpy.types.GreasePencil:
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
        text_data.size = size

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        CreateGreasePencilData.convert_2_gp()

        gp_obj = bpy.context.object
        gp_data = gp_obj.data
        layer = gp_data.layers[0]
        layer.info = text
        layer.color = GP_Color.hex_2_rgb(hex_color)
        CreateGreasePencilData.del_later(gp_obj)
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
        CreateGreasePencilData.convert_2_gp()

        gp_obj = bpy.context.object
        gp_data = gp_obj.data
        CreateGreasePencilData.del_later(gp_obj)

        return gp_data


class EditGreasePencilStroke():
    """Grease Pencil Stroke, easy to manipulate Stroke data."""

    @staticmethod
    @contextmanager
    def stroke_points(stroke: bpy.types.GPencilStroke) -> np.ndarray:
        """Get the vertices from the stroke."""
        points = np.empty(len(stroke.points) * 3, dtype='f')
        stroke.points.foreach_get('co', points)
        yield points.reshape((len(stroke.points), 3))

    @staticmethod
    def _move_stroke(stroke: bpy.types.GPencilStroke, v: Vector):
        """Move the grease pencil data."""
        move_3d = Vector((s_scale(v[0], r=True), s_scale(v[1], r=True), 0))  # apply scale
        with EditGreasePencilStroke.stroke_points(stroke) as points:
            points += move_3d
            stroke.points.foreach_set('co', points.ravel())

    @staticmethod
    def _scale_stroke(stroke: bpy.types.GPencilStroke, scale: Vector, pivot: Vector):
        """Scale the grease pencil data."""
        scale_3d = Vector((scale[0], scale[1], 1))
        pivot_3d = Vector((pivot[0], pivot[1], 0))
        with EditGreasePencilStroke.stroke_points(stroke) as points:
            points = (points - pivot_3d) * scale_3d + pivot_3d
            stroke.points.foreach_set('co', points.ravel())

    @staticmethod
    def _rotate_stroke(stroke: bpy.types.GPencilStroke, degree: int, pivot: Vector):
        """Rotate the grease pencil data."""
        pivot_3d = Vector((pivot[0], pivot[1], 0))
        with EditGreasePencilStroke.stroke_points(stroke) as vertices:
            vertices = (vertices - pivot_3d) @ np.array([[np.cos(radians(degree)), -np.sin(radians(degree)), 0],
                                                         [np.sin(radians(degree)), np.cos(radians(degree)), 0],
                                                         [0, 0, 1]]) + pivot_3d
            stroke.points.foreach_set('co', vertices.ravel())


@dataclass
class BuildGreasePencilData(GreasePencilCache):
    """Grease Pencil Data Builder, easy to manipulate grease pencil data.
    using with statement will automatically clean up the cache.else you need to call cleanup() manually.
    usage:
    with GreasePencilDataBuilder(gp_data) as gp_builder:
        gp_builder.color('Layer', '#FF0000') \
        .move('Layer', Vector((1, 1, 0))) \
        .scale('Layer', Vector((2, 2, 1)), Vector((0, 0, 0))) \
        .rotate('Layer', 90, Vector((0, 0, 0)))

    """
    gp_data: bpy.types.GreasePencil
    edit: EditGreasePencilStroke = EditGreasePencilStroke()

    def __enter__(self):
        """allow to use with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """allow to use with statement"""
        self.cleanup()  # remove cache

    @property
    def name(self) -> str:
        return self.gp_data.name

    @property
    def layer_names(self) -> list[str]:
        return [layer.info for layer in self.gp_data.layers]

    def to_2d(self) -> 'BuildGreasePencilData':
        """show the grease pencil data in 2D space."""
        self._set_space('2D')
        return self

    def to_3d(self) -> 'BuildGreasePencilData':
        """show the grease pencil data in 3D space."""
        self._set_space('3D')
        return self

    def color(self, layer_name: str, hex_color: str) -> 'BuildGreasePencilData':
        """Set the color of the grease pencil annotation layer.
        :param layer_name: The name of the layer.
        :param hex_color: The color in hex format.
        :return: instance"""
        layer = self.gp_data.layers.get(layer_name, None)
        if layer:
            layer.color = GP_Color.hex_2_rgb(hex_color)
        return self

    def link(self, context: bpy.types.Context) -> 'BuildGreasePencilData':
        """Link the grease pencil data to the node group. So that the grease pencil can be seen in the node editor."""
        if context.area.type != 'NODE_EDITOR':
            raise ValueError('Please switch to the node editor.')
        if not context.space_data.edit_tree:
            raise ValueError('Please open a node group.')

        self._link_nodegroup(context.space_data.edit_tree)
        return self

    def move(self, layer_name_or_index: Union[str, int], v: Vector) -> 'BuildGreasePencilData':
        """Move the grease pencil data."""

        layer = self._get_layer(layer_name_or_index)

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._move_stroke(stroke, v)

        return self

    def scale(self, layer_name_or_index: Union[str, int], scale: Vector, pivot: Vector) -> 'BuildGreasePencilData':
        """Scale the grease pencil data."""
        layer = self._get_layer(layer_name_or_index)

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._scale_stroke(stroke, scale, pivot)

        return self

    def rotate(self, layer_name_or_index: Union[str, int], degree: int, pivot: Vector) -> 'BuildGreasePencilData':
        """Rotate the grease pencil data."""
        layer = self._get_layer(layer_name_or_index)

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._rotate_stroke(stroke, degree, pivot)

        return self

    def join(self, other_gp_data: bpy.types.GreasePencil) -> 'BuildGreasePencilData':
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
        self.del_later(obj_list=[self_obj, tmp_obj])
        return self

    def _get_layer(self, layer_name_or_index: Union[int, str]) -> bpy.types.GPencilLayer:
        """Handle the layer.
        :param layer_name_or_index: The name or index of the layer.
        :return: The layer object.
        """
        if isinstance(layer_name_or_index, int):
            try:
                layer = self.gp_data.layers[layer_name_or_index]
            except:
                raise ValueError(f'Layer index {layer_name_or_index} not found.')
        else:
            layer = self.gp_data.layers.get(layer_name_or_index, None)
        if not layer:
            raise ValueError(f'Layer {layer_name_or_index} not found.')
        return layer

    def _link_nodegroup(self, nt: bpy.types.NodeTree, ) -> None:
        """Link the grease pencil data to the node group. So that the grease pencil can be seen in the node editor."""
        nt.grease_pencil = self.gp_data

    def _set_space(self, type: Literal['2D', '3D'],
                   layer_name_or_index: Optional[Union[str, int]] = None) -> None:
        """Convert the space of the grease pencil strokes to 2D or 3D space.
        :param type: The space to convert to, either '2D' or '3D'.
        :param layer_name: The name of the layer to convert. If None, all layers will be converted.
        """

        singler_layer = self._get_layer(layer_name_or_index) if layer_name_or_index else None
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
