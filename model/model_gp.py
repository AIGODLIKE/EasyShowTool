import bpy
import numpy as np
from mathutils import Vector, Matrix
from typing import Literal, Optional, Union, Sequence, ClassVar, Final
from contextlib import contextmanager
from dataclasses import dataclass, field
from math import radians

from .utils import VecTool, ColorTool


class MouseDetectModel:
    """MouseDetectModel Model, a base class for detect mouse position with 2d grease pencil annotation."""

    bbox_model: 'GreasePencilLayerBBox' = None

    def bind_to(self, bbox_model: 'GreasePencilLayerBBox') -> 'MouseDetectModel':
        self.bbox_model = bbox_model
        self.bbox_model.detect_model = self
        return self

    @staticmethod
    def is_point_near_point(pos: Union[Sequence, Vector], point: Union[Sequence, Vector], distance: int = 20) -> bool:
        """Check if the point is near the target point."""
        return (Vector(pos) - Vector(point)).length < distance

    def in_area(self, pos: Union[Sequence, Vector], feather: int = 0, space: Literal['r2d', 'v2d'] = 'r2d') -> bool:
        """check if the pos is in the area defined by the points
        :param pos: the position to check, in v2d/r2d space
        :param points: the points defining the area
        :param feather: the feather to expand the area, unit: pixel
        :return: True if the pos is in the area, False otherwise
        """
        x, y = pos
        points = self.bbox_model.bbox_points_r2d if space == 'r2d' else self.bbox_model.bbox_points_v2d
        top_left, top_right, bottom_left, bottom_right = points

        if feather != 0:
            top_left = (top_left[0] - feather, top_left[1] + feather)
            top_right = (top_right[0] + feather, top_right[1] + feather)
            bottom_left = (bottom_left[0] - feather, bottom_left[1] - feather)

        if top_left[0] < x < top_right[0] and bottom_left[1] < y < top_left[1]:
            return True
        return False

    def near_edge_center(self, pos: Union[Sequence, Vector], radius: int = 20, space: Literal['r2d', 'v2d'] = 'r2d') -> \
            Union[Vector, None]:
        """check if the pos is near the edge center of the area defined by the points
        :param pos: the position to check
        :param points: the points defining the area
        :param feather: the feather to expand the area, unit: pixel
        :return: True if the pos is near the edge center, False otherwise
        """
        vec_pos = Vector((pos[0], pos[1]))
        points = self.bbox_model.edge_center_points_r2d if space == 'r2d' else self.bbox_model.edge_center_points_v2d
        for point in points:
            vec_point = Vector(point)
            if (vec_pos - vec_point).length < radius:
                return vec_point
        return None

    def near_corners(self, pos: Union[Sequence, Vector], radius: int = 20, space: Literal['r2d', 'v2d'] = 'r2d') -> \
            Union[Vector, None]:
        """check if the pos is near the corners of the area defined by the bounding box points
        :param pos: the position to check
        :param points: the points defining the area
        :param feather: the feather to expand the area, unit: pixel
        :return: True if the pos is near the corners, False otherwise
        """
        vec_pos = Vector((pos[0], pos[1]))
        points = self.bbox_model.bbox_points_r2d if space == 'r2d' else self.bbox_model.bbox_points_v2d
        for point in points:
            vec_point = Vector(point)
            if (vec_pos - vec_point).length < radius:
                return vec_point
        return None

    def near_corners_extrude(self, pos: Union[Sequence, Vector], extrude: int = 15, radius: int = 15) -> Union[
        Vector, None]:

        """check if the pos is near the the corner point extrude outward by 45 deg
        :param pos: the position to check
        :param extrude: the extrude distance
        :param radius: the radius of the extrude point
        :return: True if the pos is near the corners, False otherwise
        """
        vec_pos = Vector((pos[0], pos[1]))
        points = self.bbox_model.corner_extrude_points_r2d(extrude)
        for point in points:
            if (vec_pos - point).length < radius:
                return point
        return None


@dataclass
class GreasePencilProperty:
    """Grease Pencil Property, a base class for grease pencil data get/set"""
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
        elif 0 <= index < len(self.gp_data.layers):
            self.gp_data.layers.active_index = index
        else:
            self.gp_data.layers.active_index = 0

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
    detect_model: Optional['MouseDetectModel'] = None  # avoid circular import

    @property
    def size(self) -> tuple[float, float]:
        """Return the 3d size of the bounding box."""
        return self.max_x - self.min_x, self.max_y - self.min_y

    @property
    def size_v2d(self) -> Vector:
        """Return the 2d view size of the bounding box."""
        return VecTool.loc3d_2_v2d(self.size)

    @property
    def center(self) -> tuple[float, float]:
        """Return the 3d center of the bounding box."""
        return (self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2

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
    def bbox_points_3d(self) -> tuple[tuple[float, float], ...]:
        """Return the bounding box points."""
        return self.top_left, self.top_right, self.bottom_left, self.bottom_right

    @property
    def bbox_points_v2d(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the bounding box points in node editor view."""
        return tuple(map(VecTool.loc3d_2_v2d, self.bbox_points_3d))

    @property
    def bbox_points_r2d(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the bounding box points in region 2d space."""

        return tuple(map(VecTool.v2d_2_r2d, self.bbox_points_v2d))

    @property
    def edge_center_points(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the edge center points of the bounding box."""
        top_center = (self.max_x + self.min_x) / 2, self.max_y
        bottom_center = (self.max_x + self.min_x) / 2, self.min_y
        left_center = self.min_x, (self.max_y + self.min_y) / 2
        right_center = self.max_x, (self.max_y + self.min_y) / 2
        return top_center, bottom_center, left_center, right_center

    @property
    def edge_center_points_v2d(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the edge center points of the bounding box in node editor view."""
        return tuple(map(VecTool.loc3d_2_v2d, self.edge_center_points))

    @property
    def edge_center_points_r2d(self) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the edge center points of the bounding box in region 2d space."""
        return tuple(map(VecTool.v2d_2_r2d, self.edge_center_points_v2d))

    def corner_extrude_points_r2d(self, extrude: int = 10) -> tuple[Union[tuple[float, float], Vector], ...]:
        """Return the corner extrude points of the bounding box.
        :param extrude: the extrude distance
        this is not a property because it needs an extrude distance"""
        points = self.bbox_points_r2d
        extrude_vecs = [Vector((-extrude, extrude)), Vector((extrude, extrude)), Vector((-extrude, -extrude)),
                        Vector((extrude, -extrude))]  # top_left, top_right, bottom_left, bottom_right
        new_points = [Vector(point) + vec for point, vec in zip(points, extrude_vecs)]

        return new_points

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


@dataclass
class GreasePencilLayers(GreasePencilProperty):
    @staticmethod
    def in_layer_area(gp_data: bpy.types.GreasePencil, pos: Union[Sequence, Vector], feather: int = 0,
                      space: Literal['r2d', 'v2d'] = 'r2d') -> Union[int, None]:
        """check if the pos is in the area defined by the points
        :param pos: the position to check, in v2d space
        :param points: the points defining the area
        :param feather: the feather to expand the area, unit: pixel
        :return: index of the layer if the pos is in the area, None otherwise
        """
        bboxs: list[GreasePencilLayerBBox] = [GreasePencilLayerBBox(gp_data, layer) for layer in
                                              gp_data.layers]
        for i, bbox in enumerate(bboxs):
            bbox.calc_bbox(i)
            mouse_detect = MouseDetectModel().bind_to(bbox)
            if mouse_detect.in_area(pos, feather, space):
                # print(f'In layer {bbox.gp_data.layers[i].info}')
                return bbox.last_layer_index

        return None


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
        gp_data: bpy.types.GreasePencil = gp_obj.data
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
        new_obj.scale = (size, size, size)
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
        """Rotate the grease pencil data around the pivot point."""
        pivot_3d = Vector((pivot[0], pivot[1], 0))
        angle = radians(degree)
        with EditGreasePencilStroke.stroke_points(stroke) as points:
            # use numpy to calculate the rotation
            points = ((points - pivot_3d) @ np.array([[np.cos(angle), -np.sin(angle), 0],
                                                      [np.sin(angle), np.cos(angle), 0],
                                                      [0, 0, 1]]) + pivot_3d)

            stroke.points.foreach_set('co', points.ravel())


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
    _rotate_degree: int = 0

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

    @property
    def rotate_degree(self):
        return self._rotate_degree

    @rotate_degree.setter
    def rotate_degree(self, degree: int):
        res = self.rotate_degree + degree
        if res >= 360:
            res = res - 360
        elif res < 0:
            res = 360 + res
        self._rotate_degree = res

    def set_active_layer(self, layer_name_or_index: Union[str, int]) -> 'BuildGreasePencilData':
        """Set the active grease pencil annotation layer."""
        self.active_layer_index = layer_name_or_index
        return self

    def color_active(self, hex_color: str) -> 'BuildGreasePencilData':
        """Set the color of the active grease pencil annotation layer."""
        return self.color(self.active_layer_index, hex_color)

    def color(self, layer_name_or_index: Union[str, int], hex_color: str) -> 'BuildGreasePencilData':
        """Set the color of the grease pencil annotation layer.
        :param layer_name_or_index: The name or index of the layer.
        :param hex_color: The color in hex format.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)
        if layer:
            layer.color = ColorTool.hex_2_rgb(hex_color)
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
            vec = VecTool.v2d_2_loc3d(v)
        else:
            vec = v

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._move_stroke(stroke, vec)

        return self

    def scale_active(self, scale: Vector, pivot: Vector, space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Scale the active grease pencil layer."""
        return self.scale(self.active_layer_name, scale, pivot)

    def scale(self, layer_name_or_index: Union[str, int], scale: Vector, pivot: Vector,
              space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Scale the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param scale: The scale vector.
        :param pivot: The pivot vector.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)

        if space == 'v2d':
            vec_pivot = VecTool.v2d_2_loc3d(pivot)
        else:
            vec_pivot = pivot

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._scale_stroke(stroke, scale, vec_pivot)

        return self

    def rotate_active(self, degree: int, pivot: Vector, space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Rotate the active grease pencil layer."""
        return self.rotate(self.active_layer_name, degree, pivot, space)

    def rotate(self, layer_name_or_index: Union[str, int], degree: int, pivot: Vector,
               space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Rotate the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param degree: The degree to rotate.
        :param pivot: The pivot vector.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)

        if space == 'v2d':
            vec_pivot = VecTool.v2d_2_loc3d(pivot)
        else:
            vec_pivot = pivot

        for frame in layer.frames:
            for stroke in frame.strokes:
                self.edit._rotate_stroke(stroke, degree, vec_pivot)
        self.rotate_degree = degree
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
