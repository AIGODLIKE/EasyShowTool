import bpy
import numpy as np
from mathutils import Vector, Euler
from typing import Literal, Optional, Union, ClassVar
from dataclasses import dataclass, field
from .utils import VecTool, ShootAngles, ColorTool
from .model_gp_edit import EditGreasePencilLayer, EditGreasePencilStroke


@dataclass
class GreasePencilProperty:
    """Grease Pencil Property, a base class for grease pencil data get/set"""
    gp_data: bpy.types.GreasePencil

    @property
    def name(self) -> str:
        return self.gp_data.name

    def has_active_layer(self) -> bool:
        """Check if the grease pencil data has an active layer."""
        return bool(self.gp_data.layers.active)

    @property
    def active_layer_name(self) -> str:
        """Return the active layer name."""
        return self.active_layer.info

    @active_layer_name.setter
    def active_layer_name(self, name: str):
        """Set the active layer name."""
        self.active_layer.info = name

    @property
    def active_layer(self) -> bpy.types.GPencilLayer:
        """Return the active layer."""
        return self.gp_data.layers.active

    @property
    def active_layer_index(self) -> int:
        """Return the active layer index."""
        return self.gp_data.layers.active_index

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

    def is_empty(self) -> bool:
        """Check if the grease pencil data is empty."""
        try:
            return not self.gp_data.layers
        except ReferenceError:
            return True

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
            except ValueError:
                raise ValueError(f'Layer index {layer_name_or_index} not found.')
        else:
            layer = self.gp_data.layers.get(layer_name_or_index, None)
        if not layer:
            raise ValueError(f'Layer {layer_name_or_index} not found.')
        return layer


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
            except (ReferenceError, RuntimeError):
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
    def from_text(text: str, size: int = 100) -> bpy.types.GreasePencil:
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
    def apply_transform(obj: bpy.types.Object):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True, isolate_users=True)

    @staticmethod
    def from_mesh_obj(obj: bpy.types.Object, size: int = 100,
                      euler: ShootAngles = ShootAngles.TOP) -> bpy.types.GreasePencil:
        """
        Create a grease pencil object from a mesh object and convert it to grease pencil data.
        :param obj:  the mesh object
        :param size:  in pixels
        :param euler:  the rotation of the grease pencil object
        :return:
        """
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        bpy.context.collection.objects.link(new_obj)
        new_obj.scale = (size, size, size)
        bpy.context.view_layer.objects.active = new_obj
        CreateGreasePencilData.apply_transform(new_obj)
        new_obj.rotation_euler = euler.value
        CreateGreasePencilData.apply_transform(new_obj)
        CreateGreasePencilData.convert_2_gp()
        gp_obj = bpy.context.object
        gp_data = gp_obj.data
        CreateGreasePencilData.del_later(gp_obj)

        return gp_data

    @staticmethod
    def from_gp_obj(obj: bpy.types.Object, size: int = 100,
                    euler: ShootAngles = ShootAngles.TOP) -> bpy.types.GreasePencil:
        """
        Create a grease pencil object from a grease pencil object and convert it to grease pencil data.
        Notice that modifier is not supported. Get evaluated data will crash blender.
        :param obj:  the grease pencil object
        :param size:  in pixels
        :param euler:  the rotation of the grease pencil object
        :return:
        """
        gp_data = obj.data.copy()
        new_obj = bpy.data.objects.new('tmp', gp_data)
        bpy.context.collection.objects.link(new_obj)
        bpy.context.view_layer.objects.active = new_obj
        CreateGreasePencilData.apply_transform(new_obj)
        new_obj.rotation_euler = euler.value
        CreateGreasePencilData.apply_transform(new_obj)
        CreateGreasePencilData.del_later(new_obj)

        with BuildGreasePencilData(gp_data) as gp_builder:
            for layer in gp_builder.gp_data.layers:
                gp_builder.scale(layer.info, Vector((size, size, 1)), Vector((0, 0, 0)))
        return gp_data


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
    edit_layer: EditGreasePencilLayer = EditGreasePencilLayer()

    def __enter__(self):
        """allow to use with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """allow to use with statement"""
        self.cleanup()  # remove cache

    def to_2d(self) -> 'BuildGreasePencilData':
        """show the grease pencil data in 2D space."""
        for layer in self.gp_data.layers:
            self.edit_layer.display_in_2d(layer)
        return self

    def to_3d(self) -> 'BuildGreasePencilData':
        """show the grease pencil data in 3D space."""
        for layer in self.gp_data.layers:
            self.edit_layer.display_in_3d(layer)
        return self

    def set_active_layer(self, layer_name_or_index: Union[str, int]) -> 'BuildGreasePencilData':
        """Set the active grease pencil annotation layer."""
        self.active_layer_index = layer_name_or_index
        return self

    def remove_active_layer(self) -> 'BuildGreasePencilData':
        """Delete the active grease pencil annotation layer."""
        return self.remove_layer(self.active_layer_index)

    def remove_layer(self, layer_name_or_index: Union[str, int]) -> 'BuildGreasePencilData':
        """Remove the grease pencil annotation layer."""
        layer = self._get_layer(layer_name_or_index)
        if layer:
            self.gp_data.layers.remove(layer)
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
        context.space_data.edit_tree.grease_pencil = self.gp_data
        return self

    def join(self, other_gp_data: bpy.types.GreasePencil) -> 'BuildGreasePencilData':
        """Join the grease pencil data.
        """
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

    def copy_active(self) -> 'BuildGreasePencilData':
        """Copy the active grease pencil layer."""
        self_obj = bpy.data.objects.new('tmp', self.gp_data)
        self_tmp_data = bpy.data.grease_pencils.new('tmp')
        tmp_obj = bpy.data.objects.new('tmp', self_tmp_data)
        bpy.context.collection.objects.link(self_obj)
        bpy.context.collection.objects.link(tmp_obj)
        bpy.context.view_layer.objects.active = self_obj
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        self_obj.select_set(True)
        tmp_obj.select_set(True)
        bpy.ops.gpencil.layer_duplicate_object(only_active=True)  # new layer will be send to the bottom
        self_temp_layer = self_tmp_data.layers[0]
        self_temp_layer.color = self.active_layer.color
        self.gp_data = self_obj.data
        self.del_later(obj_list=[self_obj, tmp_obj])
        return self.join(self_tmp_data)

    def move_active(self, v: Vector, space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Move the active grease pencil layer."""
        return self.move(self.active_layer_name, v, space)

    def scale_active(self, scale: Vector, pivot: Vector, space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Scale the active grease pencil layer."""
        return self.scale(self.active_layer_name, scale, pivot, space)

    def rotate_active(self, degree: int, pivot: Vector, space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Rotate the active grease pencil layer."""
        return self.rotate(self.active_layer_name, degree, pivot, space)

    def move(self, layer_name_or_index: Union[str, int], v: Vector,
             space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Move the grease pencil data.
        :param layer_name_or_index: The name or index of the layer.
        :param v: The vector to move.
        :param space: The type of the vector, either 'v2d', 'r2d', or '3d'.
        :return: instance
        """

        layer = self._get_layer(layer_name_or_index)
        vec = VecTool.v2d_2_loc3d(v) if space == 'v2d' else v
        self.edit_layer.move_layer(layer, vec)
        return self

    def scale(self, layer_name_or_index: Union[str, int], scale: Vector, pivot: Vector,
              space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Scale the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param scale: The scale vector.
        :param pivot: The pivot vector.
        :param space: The type of the vector, either 'v2d' or '3d'.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)
        vec_pivot = VecTool.v2d_2_loc3d(pivot) if space == 'v2d' else pivot
        self.edit_layer.scale_layer(layer, scale, vec_pivot)
        return self

    def rotate(self, layer_name_or_index: Union[str, int], degree: int, pivot: Vector,
               space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Rotate the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param degree: The degree to rotate.
        :param pivot: The pivot vector.
        :param space: The type of the vector, either 'v2d' or '3d'.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)
        vec_pivot = VecTool.v2d_2_loc3d(pivot) if space == 'v2d' else pivot
        self.edit_layer.rotate_layer(layer, degree, vec_pivot)
        return self
