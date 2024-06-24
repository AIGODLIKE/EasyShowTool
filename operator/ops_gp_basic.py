import bpy
from bpy.props import IntVectorProperty, FloatVectorProperty, StringProperty, BoolProperty, EnumProperty, IntProperty
from mathutils import Vector

from ..model.model_gp import CreateGreasePencilData, BuildGreasePencilData
from ..model.model_gp_bbox import GreasePencilLayerBBox
from ..model.utils import VecTool, ShootAngles
from .functions import has_edit_tree, enum_add_type_items, enum_shot_orient_items


class ENN_OT_remove_gp(bpy.types.Operator):
    bl_idname = "enn.remove_gp"
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
class ENN_OT_move_gp(bpy.types.Operator):
    bl_idname = "enn.move_gp"
    bl_label = "Move"
    bl_description = "Move the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    move_vector: IntVectorProperty(name='Move Vector', size=2, default=(50, 50))

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data:
            return {'CANCELLED'}
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.move_active(self.move_vector)
        context.area.tag_redraw()
        return {'FINISHED'}


class ENN_OT_scale_gp(bpy.types.Operator):
    bl_idname = "enn.scale_gp"
    bl_label = "Scale"
    bl_description = "Scale the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    scale_vector: bpy.props.FloatVectorProperty(name='Scale Vector', size=2, default=(1.1, 1.1))

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data:
            return {'CANCELLED'}
        bbox = GreasePencilLayerBBox(gp_data)
        bbox.calc_active_layer_bbox()
        pivot = bbox.center
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.scale_active(self.scale_vector, pivot, space='v2d')
        context.area.tag_redraw()
        return {'FINISHED'}


# noinspection PyPep8Naming
class ENN_OT_rotate_gp(bpy.types.Operator):
    bl_idname = "enn.rotate_gp"
    bl_label = "Rotate"
    bl_description = "Rotate the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    rotate_angle: bpy.props.IntProperty(name='Rotate Angle', default=30)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}

        bbox = GreasePencilLayerBBox(gp_data)
        bbox.calc_active_layer_bbox()
        pivot = bbox.center
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.rotate_active(self.rotate_angle, pivot, space='v2d')
        context.area.tag_redraw()
        return {'FINISHED'}


class ENN_OT_add_gp(bpy.types.Operator):
    bl_idname = "enn.add_gp"
    bl_label = "Add Amazing Note"
    bl_options = {'UNDO'}

    add_type: bpy.props.EnumProperty(name='Type',
                                     items=lambda _, __: enum_add_type_items(),
                                     options={'SKIP_SAVE', 'HIDDEN'})

    text: StringProperty(name="Text", default="Hello World")
    size: IntProperty(name="Size", default=100)
    obj: StringProperty(name="Object", default="", options={'SKIP_SAVE', 'HIDDEN'})
    obj_shot_angle: EnumProperty(name="Shot Orientation",
                                 items=lambda _, __: enum_shot_orient_items(),
                                 options={'SKIP_SAVE', 'HIDDEN'})

    location: FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE', 'HIDDEN'})
    use_mouse_pos: BoolProperty(default=False, options={'SKIP_SAVE', 'HIDDEN'})
    # mouse position
    mouse_pos: tuple[int, int] = (0, 0)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        return context.window_manager.invoke_props_dialog(self)

    def handle_invalid_input(self) -> bool:
        if self.add_type == 'OBJECT' and not bpy.data.objects.get(self.obj, None):
            return True
        elif self.add_type == 'TEXT' and self.text != '':
            return True
        return False

    def execute(self, context: bpy.types.Context):
        if not self.handle_invalid_input(): return {'CANCELLED'}

        font_gp_data: bpy.types.GreasePencil = None
        obj: bpy.types.Object = bpy.data.objects.get(self.obj, None)
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        vec: Vector = VecTool.r2d_2_v2d(self.mouse_pos) if self.use_mouse_pos else self.location
        gp_data: bpy.types.GreasePencil = CreateGreasePencilData.empty() if not nt.grease_pencil else nt.grease_pencil

        if self.add_type == 'TEXT':
            font_gp_data = CreateGreasePencilData.from_text(self.text, self.size)
        elif self.add_type == 'OBJECT':
            euler = getattr(ShootAngles, self.obj_shot_angle)
            if obj.type == 'MESH':
                font_gp_data = CreateGreasePencilData.from_mesh_obj(obj, euler=euler)
            elif obj.type == 'GPENCIL':
                font_gp_data = CreateGreasePencilData.from_gp_obj(obj, euler=euler)
            else:
                return {'CANCELLED'}

        if not font_gp_data: return {'CANCELLED'}

        color = context.scene.enn_palette_group.palette.colors.active.color
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.link(context).join(font_gp_data) \
                .set_active_layer(-1).move_active(vec, space='v2d').color_active(color=color).to_2d()

        return {'FINISHED'}


def register():
    from bpy.utils import register_class

    register_class(ENN_OT_add_gp)
    register_class(ENN_OT_remove_gp)
    register_class(ENN_OT_move_gp)
    register_class(ENN_OT_rotate_gp)
    register_class(ENN_OT_scale_gp)


def unregister():
    from bpy.utils import unregister_class

    unregister_class(ENN_OT_move_gp)
    unregister_class(ENN_OT_rotate_gp)
    unregister_class(ENN_OT_scale_gp)
    unregister_class(ENN_OT_remove_gp)
    unregister_class(ENN_OT_add_gp)
