import bpy
import numpy as np
from mathutils import Vector
from typing import Literal, Optional, Union, Sequence, ClassVar, Final
from contextlib import contextmanager
from dataclasses import dataclass, field
from math import radians


class DPI:
    """DPI utility class. use to convert between view 2d , region 2d and 3d space."""

    @staticmethod
    def _size_2(v: float, r: bool = False) -> float:
        """
        convert grease pencil annotation location between 2d space to 3d space
        :param v: value
        :param r: reverse False: 3d -> 2d, True: 2d -> 3d
        :return: value
        """
        scale = bpy.context.preferences.system.ui_scale
        return v / scale if not r else v * scale

    @staticmethod
    def _vec_2(v: Vector, r: bool = False) -> Vector:
        """
        convert grease pencil annotation location between 2d space to 3d space
        :param v: value
        :param r: reverse False: 3d -> 2d, True: 2d -> 3d
        :return: value
        """
        scale = bpy.context.preferences.system.ui_scale
        return Vector((v[0] / scale, v[1] / scale, 1)) if not r else Vector((v[0] * scale, v[1] * scale, 1))

    @property
    def ui_scale(self) -> float:
        return bpy.context.preferences.system.ui_scale

    @staticmethod
    def r2d_2_v2d(location: Union[Vector, Sequence]) -> Vector:
        """Convert region 2d space point to node editor 2d view."""
        ui_scale = bpy.context.preferences.system.ui_scale
        x, y = bpy.context.region.view2d.region_to_view(location[0], location[1])
        return Vector((x / ui_scale, y / ui_scale))

    @staticmethod
    def v2d_2_r2d(location: Union[Vector, Sequence]) -> Vector:
        """Convert node editor 2d view point to region 2d space."""
        ui_scale = bpy.context.preferences.system.ui_scale
        x, y = bpy.context.region.view2d.view_to_region(location[0] * ui_scale, location[1] * ui_scale, clip=False)
        return Vector((x, y))

    @staticmethod
    def loc3d_2_v2d(location: Union[Vector, Sequence]) -> Vector:
        """Convert 3D space point to node editor 2d space."""
        return Vector((DPI._size_2(location[0]), DPI._size_2(location[1])))

    @staticmethod
    def v2d_2_loc3d(location: Union[Vector, Sequence]) -> Vector:
        """Convert 2D space point to 3D space."""
        return Vector((DPI._size_2(location[0], r=True), DPI._size_2(location[1], r=True)))


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
class GreasePencilProperty:
    """Grease Pencil Property, a base class for grease pencil data."""
    gp_data: bpy.types.GreasePencil

    @property
    def name(self) -> str:
        return self.gp_data.name

    @property
    def active_layer_name(self) -> str:
        """Return the active layer name."""
        return self.active_layer.info

    @property
    def active_layer(self) -> bpy.types.GPencilLayer:
        """Return the active layer."""
        return self.gp_data.layers.active

    @active_layer_name.setter
    def active_layer_name(self, name: str):
        """Set the active layer name."""
        self.active_layer.info = name

    @property
    def active_layer_index(self) -> int:
        """Return the active layer index."""
        return self.gp_data.layers.active_index

    @active_layer_index.setter
    def active_layer_index(self, index: int):
        """Set the active layer index."""
        if index < 0:
            self.gp_data.layers.active_index = len(self.gp_data.layers) - 1
        elif index >= len(self.gp_data.layers):
            self.gp_data.layers.active_index = 0
        else:
            self.gp_data.layers.active_index = index

    def active_next_layer(self):
        """Set the next layer as active."""
        self.active_layer_index += 1

    def active_prev_layer(self):
        """Set the last layer as active."""
        self.active_layer_index -= 1

    @property
    def layer_names(self) -> list[str]:
        return [layer.info for layer in self.gp_data.layers]

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
    #
    last_layer_index: int = None

    @property
    def size(self) -> tuple[float, float]:
        """Return the 3d size of the bounding box."""
        return self.max_x - self.min_x, self.max_y - self.min_y

    @property
    def center(self) -> tuple[float, float]:
        """Return the 3d center of the bounding box."""
        return (self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2

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
    def bbox_points_3d(self) -> tuple[tuple[float, float], ...]:
        """Return the bounding box points."""
        return self.top_left, self.top_right, self.bottom_left, self.bottom_right

    @property
    def bbox_points_v2d(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the bounding box points in node editor view."""
        return tuple(map(DPI.loc3d_2_v2d, self.bbox_points_3d))

    @property
    def bbox_points_r2d(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the bounding box points in region 2d space."""

        return tuple(map(DPI.v2d_2_r2d, self.bbox_points_v2d))

    @staticmethod
    def _calc_stroke_bbox(stroke: bpy.types.GPencilStroke) -> tuple[float, float, float, float]:
        """
        Calculate the bounding box of a stroke.
        :param stroke:
        :return:
        """
        with EditGreasePencilStroke.stroke_points(stroke) as vertices:
            max_xyz_id = np.argmax(vertices, axis=0)
            min_xyz_id = np.argmin(vertices, axis=0)

            max_x = float(vertices[max_xyz_id[0], 0])
            max_y = float(vertices[max_xyz_id[1], 1])
            min_x = float(vertices[min_xyz_id[0], 0])
            min_y = float(vertices[min_xyz_id[1], 1])

        return max_x, min_x, max_y, min_y

    def calc_active_layer_bbox(self, frame: int = 0) -> tuple[tuple[float, float], ...]:
        """
        Calculate the bounding box of the active grease pencil annotation layer.
        :param frame: calc this frame
        :return: The bounding box of the grease pencil annotation.
            return in position of 2d space
            positions = (
                (-1, 1), (1, 1),
                (-1, -1), (1, -1))

            indices = ((0, 1, 2), (2, 1, 3))
        """
        layer = self.active_layer
        if not layer:
            raise ValueError('Active layer not found.')

        return self.calc_bbox(layer.info, frame)

    def calc_bbox(self, layer_name_or_inedx: Union[str, int], frame: int = 0) -> None:
        """
        Calculate the bounding box of the grease pencil annotation.
        :param layer_name_or_inedx: The name or index of the layer.
        :param frame: calc this frame
        :return: The bounding box of the grease pencil annotation.
            return in position of 2d space
            positions = (
                (-1, 1), (1, 1),
                (-1, -1), (1, -1))

            indices = ((0, 1, 2), (2, 1, 3))
        """

        layer = self._get_layer(layer_name_or_inedx)
        if not layer:
            raise ValueError(f'Layer {layer_name_or_inedx} not found.')

        frame = layer.frames[frame]
        if not frame:
            raise ValueError(f'Frame {frame} not found.')

        x_list = []
        y_list = []
        for stroke in frame.strokes:
            max_x, min_x, max_y, min_y = self._calc_stroke_bbox(stroke)
            x_list.extend([max_x, min_x])
            y_list.extend([max_y, min_y])

        self.max_x = max(x_list)
        self.min_x = min(x_list)
        self.max_y = max(y_list)
        self.min_y = min(y_list)
        self.last_layer_index = [i for i, l in enumerate(self.gp_data.layers) if l == layer][0]

    def in_area(self, pos: Union[Sequence, Vector], feather: int = 20, space: Literal['r2d', 'v2d'] = 'r2d') -> bool:
        """check if the pos is in the area defined by the points
        :param pos: the position to check, in v2d space
        :param points: the points defining the area
        :param feather: the feather to expand the area, unit: pixel
        :return: True if the pos is in the area, False otherwise
        """
        x, y = pos
        points = self.bbox_points_r2d if space == 'r2d' else self.bbox_points_v2d
        top_left, top_right, bottom_left, bottom_right = points

        top_left = (top_left[0] - feather, top_left[1] + feather)
        top_right = (top_right[0] + feather, top_right[1] + feather)
        bottom_left = (bottom_left[0] - feather, bottom_left[1] - feather)

        if top_left[0] < x < top_right[0] and bottom_left[1] < y < top_left[1]:
            return True
        return False


@dataclass
class GreasePencilLayers(GreasePencilProperty):
    @staticmethod
    def in_layer_area(gp_data: bpy.types.GreasePencil, pos: Union[Sequence, Vector], feather: int = 20,
                      space: Literal['r2d', 'v2d'] = 'r2d') -> Union[int, None]:
        """check if the pos is in the area defined by the points
        :param pos: the position to check, in v2d space
        :param points: the points defining the area
        :param feather: the feather to expand the area, unit: pixel
        :return: True if the pos is in the area, False otherwise
        """
        bboxs: list[GreasePencilLayerBBox] = [GreasePencilLayerBBox(gp_data, layer) for layer in
                                              gp_data.layers]
        for i, bbox in enumerate(bboxs):
            bbox.calc_bbox(i)

        for bbox in bboxs.reverse():  # top first
            if bbox.in_area(pos, feather, space):
                return bbox.last_layer_index
        return False


class GreasePencilCache:
    """Grease Pencil Cache, cache the grease pencil objects."""
    # cache the grease pencil objects
    # this is a class variable, so it will be shared among all instances / subclasses instances
    tmp_objs: ClassVar[list[bpy.types.Object]] = []

    @classmethod
    def cleanup(cls):
        """Remove the cache."""
        for obj in cls.tmp_objs:
            try:
                bpy.data.objects.remove(obj)
            except:
                pass
        cls.tmp_objs.clear()

    @classmethod
    def del_later(cls, obj: Optional[bpy.types.Object] = None, obj_list: Optional[list[bpy.types.Object]] = None):
        """Delete the grease pencil object later."""
        if obj:
            cls.tmp_objs.append(obj)
        if obj_list:
            cls.tmp_objs.extend(obj_list)


class CreateGreasePencilData(GreasePencilCache):
    """Grease Pencil Data Factory, a static class that makes it easy to create grease pencil data.
    below properties are class variables, using in the convert_2_gp method
    :param seam:  Add seam to the grease pencil data.
    :param faces: Add faces to the grease pencil data.
    :param offset: The offset of the grease pencil data.
    """

    seam: ClassVar[bool] = False
    faces: ClassVar[bool] = False
    offset: ClassVar[float] = 0.01

    @classmethod
    def convert_2_gp(cls, keep_original: bool = False):
        bpy.ops.object.convert(target='GPENCIL', seams=cls.seam, faces=cls.faces, offset=cls.offset,
                               keep_original=keep_original)

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
        Create a text object in the scene and convert it to grease pencil data.
        :param text:  the text to display
        :param size:  in pixels
        :return: the grease pencil data
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
        CreateGreasePencilData.del_later(gp_obj)
        return gp_data

    @staticmethod
    def from_mesh_obj(obj: bpy.types.Object, size: int = 100) -> bpy.types.GreasePencil:
        """
        Create a grease pencil object from a mesh object and convert it to grease pencil data.
        :param obj:  the mesh object
        :return:
        """
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        bpy.context.collection.objects.link(new_obj)
        new_obj._size_2 = (size, size, size)
        bpy.context.view_layer.objects.active = new_obj
        bpy.ops.object.select_all(action='DESELECT')
        new_obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        CreateGreasePencilData.convert_2_gp()

        gp_obj = bpy.context.object
        gp_data = gp_obj.data
        CreateGreasePencilData.del_later(gp_obj)

        return gp_data

    @staticmethod
    def from_gp_obj(obj: bpy.types.Object, size: int = 100) -> bpy.types.GreasePencil:
        """
        Create a grease pencil object from a grease pencil object and convert it to grease pencil data.
        Notice that modifier is not supported. Get evaluated data will crash blender.
        :param obj:  the grease pencil object
        :return:
        """
        gp_data = obj.data.copy()
        with BuildGreasePencilData(gp_data) as gp_builder:
            for layer in gp_builder.gp_data.layers:
                gp_builder.scale(layer.info, Vector((size, size, 1)), Vector((0, 0, 0)))
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
        move_3d = Vector((v[0], v[1], 0))
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
class BuildGreasePencilData(GreasePencilCache, GreasePencilProperty):
    """Grease Pencil Data Builder, easy to manipulate grease pencil data.
    using with statement will automatically clean up the cache.else you need to call cleanup() manually.
    usage:
    with GreasePencilDataBuilder(gp_data) as gp_builder:
        gp_builder.color('Layer', '#FF0000') \
        .move('Layer', Vector((1, 1, 0))) \
        .scale('Layer', Vector((2, 2, 1)), Vector((0, 0, 0))) \
        .rotate('Layer', 90, Vector((0, 0, 0)))

    """
    edit: EditGreasePencilStroke = EditGreasePencilStroke()

    def __enter__(self):
        """allow to use with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """allow to use with statement"""
        self.cleanup()  # remove cache

    def to_2d(self) -> 'BuildGreasePencilData':
        """show the grease pencil data in 2D space."""
        self._set_display_mode('2D')
        return self

    def to_3d(self) -> 'BuildGreasePencilData':
        """show the grease pencil data in 3D space."""
        self._set_display_mode('3D')
        return self

    def color(self, layer_name_or_index: Union[str, int], hex_color: str) -> 'BuildGreasePencilData':
        """Set the color of the grease pencil annotation layer.
        :param layer_name_or_index: The name or index of the layer.
        :param hex_color: The color in hex format.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)
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

    def move_active(self, v: Vector, space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Move the active grease pencil layer."""
        return self.move(self.active_layer_name, v, space)

    def move(self, layer_name_or_index: Union[str, int], v: Vector,
             space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Move the grease pencil data.
        :param layer_name_or_index: The name or index of the layer.
        :param v: The vector to move.
        :param space: The type of the vector, either 'v2d', 'r2d', or '3d'.
        :return: instance
        """

        layer = self._get_layer(layer_name_or_index)

        if space == 'v2d':
            vec = DPI.v2d_2_loc3d(v)
        else:
            vec = v

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._move_stroke(stroke, vec)

        return self

    # TODO: add support for 2D view space pivot point.
    def scale(self, layer_name_or_index: Union[str, int], scale: Vector, pivot: Vector) -> 'BuildGreasePencilData':
        """Scale the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param scale: The scale vector.
        :param pivot: The pivot vector.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._scale_stroke(stroke, scale, pivot)

        return self

    def rotate(self, layer_name_or_index: Union[str, int], degree: int, pivot: Vector) -> 'BuildGreasePencilData':
        """Rotate the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param degree: The degree to rotate.
        :param pivot: The pivot vector.
        :return: instance"""
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

    def _link_nodegroup(self, nt: bpy.types.NodeTree, ) -> None:
        """Link the grease pencil data to the node group. So that the grease pencil can be seen in the node editor."""
        nt.grease_pencil = self.gp_data

    def _set_display_mode(self, type: Literal['2D', '3D'],
                          layer_name_or_index: Optional[Union[str, int]] = None) -> None:
        """Convert the display_mode of the grease pencil strokes to 2D or 3D space.
        :param type: The space to convert to, either '2D' or '3D'.
        :param layer_name_or_index: The name or index of the layer to convert. If None, all layers will be converted.
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
