import bpy
import numpy as np
from mathutils import Vector, Euler, Color
from typing import Literal, Optional, Union, ClassVar
from dataclasses import dataclass, field
from .utils import VecTool
from .data_enums import ShootAngles
from .model_gp_edit import EditGreasePencilLayer
from .model_gp_property import GreasePencilProperty, GPencilStroke
from .model_gp_bbox import GPencilLayerBBox


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
    def ensure_context_obj():
        """Ensure there is a context object to make bpy.ops.object work."""
        if bpy.context.object: return
        c_obj = bpy.data.objects.new('tmp_context', None)
        bpy.context.collection.objects.link(c_obj)
        bpy.context.view_layer.objects.active = c_obj
        CreateGreasePencilData.del_later(c_obj)

    @staticmethod
    def empty() -> bpy.types.GreasePencil:
        """Create an empty grease pencil data."""
        CreateGreasePencilData.ensure_context_obj()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.gpencil_add(type='EMPTY')
        obj = bpy.context.object
        gp_data = obj.data
        CreateGreasePencilData.del_later(obj)
        return gp_data

    @staticmethod
    def from_text(text: str, size: int = 100, font: str = 'Bfont Regular') -> bpy.types.GreasePencil:
        """
        Create a text object in the scene and convert it to grease pencil data.
        :param text:  the text to display
        :param size:  in pixels
        :param font:  the font name
        :return: the grease pencil data
        """
        bpy.ops.object.text_add()
        obj = bpy.context.object
        text_data = obj.data
        text_data.body = text
        text_data.size = size
        text_data.font = bpy.data.fonts[font]

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        CreateGreasePencilData.convert_2_gp()

        gp_obj = bpy.context.object
        CreateGreasePencilData.apply_transform(gp_obj)

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
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        obj.location = (0, 0, 0)  # set origin to geometry, and clear location, so that the object will be at the center
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
        CreateGreasePencilData.convert_2_gp()
        gp_obj = bpy.context.object
        gp_obj.rotation_euler = euler.value
        CreateGreasePencilData.apply_transform(gp_obj)
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
        # new_obj = bpy.data.objects.new('tmp', gp_data)
        new_obj = obj.copy()
        new_obj.data = gp_data
        bpy.context.collection.objects.link(new_obj)
        bpy.context.view_layer.objects.active = new_obj
        CreateGreasePencilData.apply_transform(new_obj)
        new_obj.rotation_euler = euler.value
        for mod in new_obj.grease_pencil_modifiers:
            bpy.ops.object.gpencil_modifier_apply(apply_as='DATA', modifier=mod.name)
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

    def is_2d(self):
        return self.edit_layer.is_in_2d(self.active_layer)

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

    def set_active_layer(self, layer_name_or_index: str | int) -> 'BuildGreasePencilData':
        """Set the active grease pencil annotation layer."""
        if isinstance(layer_name_or_index, int):
            self.active_layer_index = layer_name_or_index
        elif isinstance(layer_name_or_index, str):
            for i, layer in enumerate(self.gp_data.layers):
                if layer.info == layer_name_or_index:
                    self.active_layer_index = i
                    break
        return self

    def remove_active_layer(self) -> 'BuildGreasePencilData':
        """Delete the active grease pencil annotation layer."""
        return self.remove_layer(self.active_layer_index)

    def remove_layer(self, layer_name_or_index: str | int) -> 'BuildGreasePencilData':
        """Remove the grease pencil annotation layer."""
        layer = self._get_layer(layer_name_or_index)
        if layer:
            self.gp_data.layers.remove(layer)
        return self

    def color_active(self, color: Color) -> 'BuildGreasePencilData':
        """Set the color of the active grease pencil annotation layer."""

        return self.color(self.active_layer_index, color)

    def opacity_active(self, opacity: float) -> 'BuildGreasePencilData':
        """Set the opacity of the active grease pencil annotation layer."""
        return self.opacity(self.active_layer_index, opacity)

    def thickness_active(self, thickness: int = 1) -> 'BuildGreasePencilData':
        return self.thickness(self.active_layer_index, thickness)

    def opacity(self, layer_name_or_index: str | int, opacity: float) -> 'BuildGreasePencilData':
        """Set the opacity of the grease pencil annotation layer."""
        layer = self._get_layer(layer_name_or_index)
        if layer:
            layer.annotation_opacity = opacity
        return self

    def color(self, layer_name_or_index: str | int, color: Color = None) -> 'BuildGreasePencilData':
        """Set the color of the grease pencil annotation layer.
        :param layer_name_or_index: The name or index of the layer.
        :param hex_color: The color in hex format.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)
        if layer:
            layer.color = color

        return self

    def thickness(self, layer_name_or_index: str | int, thickness: int) -> 'BuildGreasePencilData':
        """Set the thickness of the grease pencil annotation layer."""
        layer = self._get_layer(layer_name_or_index)
        if layer:
            layer.thickness = thickness
        return self

    def remove_svg_bound(self) -> 'BuildGreasePencilData':
        """Remove the svg bound of the grease pencil data."""
        if not (layer := self._get_layer(self.active_layer_index)):
            return self

        stroke_remove = None
        frame = layer.frames[0]
        bbox = GPencilLayerBBox(self.gp_data)
        bbox.calc_active_layer_bbox()

        for i, stroke in enumerate(frame.strokes):
            points = GPencilStroke.get_stroke_points(stroke)
            min_x = np.min(points[:, 0])
            max_x = np.max(points[:, 0])
            min_y = np.min(points[:, 1])
            max_y = np.max(points[:, 1])

            if len(stroke.points) == 37:  # blender svg bound points num
                if min_x == bbox.min_x and max_x == bbox.max_x and min_y == bbox.min_y and max_y == bbox.max_y:
                    stroke_remove = stroke
                    break

        if stroke_remove:
            frame.strokes.remove(stroke_remove)

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
        self_temp_layer.rotation = self.active_layer.rotation
        self.gp_data = self_obj.data
        self.del_later(obj_list=[self_obj, tmp_obj])
        return self.join(self_tmp_data)

    def store_active(self) -> 'BuildGreasePencilData':
        """Store the active grease pencil layer."""
        self.active_layer_points = self.edit_layer.get_layer_points(self.active_layer)
        return self

    def restore_active(self) -> 'BuildGreasePencilData':
        """Restore the active grease pencil layer."""
        if hasattr(self, 'active_layer_points'):
            self.edit_layer.set_layer_points(self.active_layer, self.active_layer_points)
        return self

    def move_active(self, v: Vector, space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Move the active grease pencil layer."""
        return self.move(self.active_layer_name, v, space)

    def scale_active(self, scale: Vector, pivot: Vector, space: Literal['v2d', '3d'] = '3d',
                     local: bool = False) -> 'BuildGreasePencilData':
        """Scale the active grease pencil layer."""
        return self.scale(self.active_layer_name, scale, pivot, space, local)

    def rotate_active(self, degree: int | float, pivot: Vector,
                      space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Rotate the active grease pencil layer."""
        return self.rotate(self.active_layer_name, degree, pivot, space)

    def fit_size(self, size: Vector, keep_aspect_ratio: bool = True) -> 'BuildGreasePencilData':
        """Fit the size of the active grease pencil layer."""
        bbox = GPencilLayerBBox(self.active_layer)
        bbox.gp_data = self.gp_data
        bbox.calc_bbox(self.active_layer_index)
        scale = Vector((size[0] / (bbox.max_x - bbox.min_x), size[1] / (bbox.max_y - bbox.min_y)))
        if keep_aspect_ratio:
            scale = Vector((min(scale), min(scale)))
        self.edit_layer.scale_layer(self.active_layer, scale, bbox.center)

        return self

    def move(self, layer_name_or_index: str | int, v: Vector,
             space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Move the grease pencil data.
        :param layer_name_or_index: The name or index of the layer.
        :param v: The vector to move.
        :param space: The type of the vector, either 'v2d', 'r2d', or '3d'.
        :return: instance
        """

        layer = self._get_layer(layer_name_or_index)
        vec = Vector(v) if space == '3d' else VecTool.v2d_2_loc3d(Vector(v))
        self.edit_layer.move_layer(layer, vec)
        return self

    def scale(self, layer_name_or_index: str | int, scale: Vector, pivot: Vector,
              space: Literal['v2d', '3d'] = '3d', local: bool = False) -> 'BuildGreasePencilData':
        """Scale the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param scale: The scale vector.
        :param pivot: The pivot vector.
        :param space: The type of the vector, either 'v2d' or '3d'.
        :param local: The local scale flag.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)
        vec_pivot = pivot if space == '3d' else VecTool.v2d_2_loc3d(pivot)
        self.edit_layer.scale_layer(layer, scale, vec_pivot, local)
        return self

    def rotate(self, layer_name_or_index: str | int, degree: int | float, pivot: Vector,
               space: Literal['v2d', '3d'] = '3d') -> 'BuildGreasePencilData':
        """Rotate the grease pencil data.
        The pivot point should be in 3D space.
        :param layer_name_or_index: The name or index of the layer.
        :param degree: The degree to rotate.
        :param pivot: The pivot vector.
        :param space: The type of the vector, either 'v2d' or '3d'.
        :return: instance"""
        layer = self._get_layer(layer_name_or_index)
        vec_pivot = pivot if space == '3d' else VecTool.v2d_2_loc3d(pivot)
        self.edit_layer.rotate_layer(layer, degree, vec_pivot)
        return self
