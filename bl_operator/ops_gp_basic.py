import bpy
from bpy.props import IntVectorProperty, FloatVectorProperty, StringProperty, BoolProperty, EnumProperty, IntProperty
from mathutils import Vector

from ..model.model_gp import CreateGreasePencilData, BuildGreasePencilData
from ..model.model_gp_bbox import GPencilLayerBBox
from ..model.utils import VecTool
from ..model.data_enums import ShootAngles, GPAddTypes
from .functions import has_edit_tree, get_pos_layer_index, load_icon_svg, \
    get_edit_tree_gp_data, ensure_builtin_font

from ..public_path import get_pref


class EST_OT_toggle_gp_space(bpy.types.Operator):
    bl_idname = "est.toggle_gp_space"
    bl_label = "Toggle Space"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            if gp_data_builder.is_2d():
                gp_data_builder.to_3d()
            else:
                gp_data_builder.to_2d()
        return {'FINISHED'}


class EST_OT_remove_gp(bpy.types.Operator):
    bl_idname = "est.remove_gp"
    bl_label = "Remove"
    bl_description = "Remove the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.remove_active_layer()
        return {'FINISHED'}


# noinspection PyPep8Naming
class EST_OT_move_gp(bpy.types.Operator):
    bl_idname = "est.move_gp"
    bl_label = "Move"
    bl_description = "Move the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    move_vector: IntVectorProperty(name='Move Vector', size=2, default=(50, 50))

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        if not (gp_data := get_edit_tree_gp_data(context)):
            return {'CANCELLED'}
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.move_active(self.move_vector)
        context.area.tag_redraw()
        return {'FINISHED'}


class EST_OT_scale_gp(bpy.types.Operator):
    bl_idname = "est.scale_gp"
    bl_label = "Scale"
    bl_description = "Scale the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    scale_vector: bpy.props.FloatVectorProperty(name='Scale Vector', size=2, default=(1.1, 1.1))

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        if not (gp_data := get_edit_tree_gp_data(context)):
            return {'CANCELLED'}
        bbox = GPencilLayerBBox(gp_data)
        bbox.calc_active_layer_bbox()
        pivot = bbox.center
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.scale_active(self.scale_vector, pivot, space='v2d')
        context.area.tag_redraw()
        return {'FINISHED'}


# noinspection PyPep8Naming
class EST_OT_rotate_gp(bpy.types.Operator):
    bl_idname = "est.rotate_gp"
    bl_label = "Rotate"
    bl_description = "Rotate the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    rotate_angle: bpy.props.IntProperty(name='Rotate Angle', default=30)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        if not (gp_data := get_edit_tree_gp_data(context)):
            return {'CANCELLED'}

        bbox = GPencilLayerBBox(gp_data)
        bbox.calc_active_layer_bbox()
        pivot = bbox.center
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.rotate_active(self.rotate_angle, pivot, space='v2d')
        context.area.tag_redraw()
        return {'FINISHED'}


class EST_OT_add_gp(bpy.types.Operator):
    bl_idname = "est.add_gp"
    bl_label = "Add Amazing Note"
    bl_options = {'UNDO'}

    add_type: bpy.props.EnumProperty(name='Type',
                                     items=lambda _, __: GPAddTypes.enum_items(), )
    # add source
    text: StringProperty(name="Text", default="Hello World")
    size: IntProperty(name="Size", default=100)
    obj: StringProperty(name="Object", default="")
    obj_shot_angle: EnumProperty(name="Shot Orientation",
                                 items=lambda _, __: ShootAngles.enum_items(), )
    icon: StringProperty(name="Icon", default="BLENDER")
    # location
    location: FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE', 'HIDDEN'})
    use_mouse_pos: BoolProperty(default=False, options={'SKIP_SAVE', 'HIDDEN'})
    mouse_pos: tuple[int, int] = (0, 0)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        ori_active_obj = context.object
        font_gp_data: bpy.types.GreasePencil = None
        obj: bpy.types.Object = bpy.data.objects.get(self.obj)
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        vec: Vector = VecTool.r2d_2_v2d(self.mouse_pos) if self.use_mouse_pos else self.location
        gp_data: bpy.types.GreasePencil = CreateGreasePencilData.empty() if not nt.grease_pencil else nt.grease_pencil

        if self.add_type == 'TEXT':
            ensure_builtin_font()
            font_gp_data = CreateGreasePencilData.from_text(self.text, self.size, context.scene.est_gp_text_font.name)
        elif self.add_type == 'OBJECT':
            euler = getattr(ShootAngles, self.obj_shot_angle)
            if obj.type == 'MESH':
                font_gp_data = CreateGreasePencilData.from_mesh_obj(obj, self.size, euler=euler)
            elif obj.type == 'GPENCIL':
                font_gp_data = CreateGreasePencilData.from_gp_obj(obj, self.size, euler=euler)
            else:
                return {'CANCELLED'}
        elif self.add_type == 'BL_ICON':
            icon_obj = load_icon_svg(self.icon)
            if not icon_obj: return {'CANCELLED'}
            font_gp_data = CreateGreasePencilData.from_gp_obj(icon_obj, self.size, euler=ShootAngles.FRONT)
            CreateGreasePencilData.del_later(icon_obj)
        if not font_gp_data: return {'CANCELLED'}

        color = context.scene.est_palette_color
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.link(context).join(font_gp_data) \
                .set_active_layer(-1) \
                .move_active(vec, space='v2d') \
                .fit_size(Vector((self.size, self.size)), keep_aspect_ratio=True) \
                .color_active(color=color) \
                .to_2d()
            if self.add_type == 'BL_ICON' and get_pref().gp_performance.try_remove_svg_bound_stroke:
                gp_data_builder.remove_svg_bound()

        context.view_layer.objects.active = ori_active_obj

        return {'FINISHED'}


class EST_OT_gp_set_active_layer_color(bpy.types.Operator):
    bl_idname = 'est.gp_set_active_layer_color'
    bl_label = 'Set Active Layer Color'
    bl_description = 'Set the active layer color of the Grease Pencil Object'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        if not (gp_data := get_edit_tree_gp_data(context)):
            return {'CANCELLED'}

        if (layer_index := get_pos_layer_index(gp_data, (event.mouse_region_x, event.mouse_region_y),
                                               local=context.scene.est_gp_transform_mode)) is None:
            return {'FINISHED'}

        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.active_layer_index = layer_index
            color = context.scene.est_palette_color
            gp_data_builder.color_active(color=color)
        return {'FINISHED'}


def register():
    from bpy.utils import register_class

    register_class(EST_OT_toggle_gp_space)
    register_class(EST_OT_add_gp)
    register_class(EST_OT_remove_gp)
    register_class(EST_OT_move_gp)
    register_class(EST_OT_rotate_gp)
    register_class(EST_OT_scale_gp)
    register_class(EST_OT_gp_set_active_layer_color)


def unregister():
    from bpy.utils import unregister_class

    unregister_class(EST_OT_move_gp)
    unregister_class(EST_OT_rotate_gp)
    unregister_class(EST_OT_scale_gp)
    unregister_class(EST_OT_remove_gp)
    unregister_class(EST_OT_add_gp)
    unregister_class(EST_OT_toggle_gp_space)
    unregister_class(EST_OT_gp_set_active_layer_color)
