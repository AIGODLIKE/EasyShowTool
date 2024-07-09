import bpy
from bpy.props import IntVectorProperty, FloatVectorProperty, StringProperty, BoolProperty, EnumProperty, IntProperty, \
    PointerProperty
from mathutils import Vector

from ..model.model_gp import CreateGreasePencilData, BuildGreasePencilData
from ..model.model_gp_bbox import GPencilLayerBBox
from ..model.utils import VecTool, ShootAngles
from .functions import has_edit_tree, enum_add_type_items, enum_shot_orient_items, in_layer_area
from .ops_gp_modal import ENN_OT_add_gp_modal
from ..public_path import get_pref


class ENN_OT_toggle_gp_space(bpy.types.Operator):
    bl_idname = "enn.toggle_gp_space"
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
        bbox = GPencilLayerBBox(gp_data)
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

        bbox = GPencilLayerBBox(gp_data)
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
                                     items=lambda _, __: enum_add_type_items(), )

    text: StringProperty(name="Text", default="Hello World")
    size: IntProperty(name="Size", default=100)
    obj: StringProperty(name="Object", default="")
    obj_shot_angle: EnumProperty(name="Shot Orientation",
                                 items=lambda _, __: enum_shot_orient_items(), )

    location: FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE', 'HIDDEN'})
    use_mouse_pos: BoolProperty(default=False, options={'SKIP_SAVE', 'HIDDEN'})
    # mouse position
    mouse_pos: tuple[int, int] = (0, 0)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    # def draw(self, context):
    #     layout = self.layout
    #     row = layout.row()
    #     row.prop(self, 'add_type', expand=True)
    #     layout.prop(self, 'size')
    #     if self.add_type == 'TEXT':
    #         layout.prop(self, 'text')
    #     elif self.add_type == 'OBJECT':
    #         layout.prop(context.window_manager, 'enn_gp_obj')
    #         layout.prop(self, 'obj_shot_angle')

    def invoke(self, context, event):
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        font_gp_data: bpy.types.GreasePencil = None
        obj: bpy.types.Object = bpy.data.objects.get(self.obj)
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


class ENN_OT_gp_set_active_layer_color(bpy.types.Operator):
    bl_idname = 'enn.gp_set_active_layer_color'
    bl_label = 'Set Active Layer Color'
    bl_description = 'Set the active layer color of the Grease Pencil Object'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        try:
            layer_index = in_layer_area(gp_data, (event.mouse_region_x, event.mouse_region_y))
        except ReferenceError:  # ctrl z
            layer_index = None
        except AttributeError:  # switch to other tool
            layer_index = None
        if layer_index is None:
            return {'FINISHED'}

        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.active_layer_index = layer_index
            color = context.scene.enn_palette_group.palette.colors.active.color
            gp_data_builder.color_active(color=color)
        return {'FINISHED'}


class ENN_PT_gn_edit_panel(bpy.types.Panel):
    bl_label = "Edit Grease Pencil Text"
    bl_idname = "ENN_PT_gn_edit_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "enn_gp_size")

        box = layout.box()
        box.label(text="New")
        row = box.row()
        row.prop(context.scene, "enn_gp_add_type", expand=True)

        if context.scene.enn_gp_add_type == 'TEXT':
            box.prop(context.scene, "enn_gp_text")
        elif context.scene.enn_gp_add_type == 'OBJECT':
            box.prop(context.scene, "enn_gp_obj")
            box.prop(context.scene, "enn_gp_obj_shot_angle")
        # box.operator(ENN_OT_add_gp_modal.bl_idname)

        if context.scene.enn_palette_group:
            box = layout.box()
            box.label(text="Palette")
            box.template_palette(context.scene.enn_palette_group, "palette", color=True)

        if get_pref().debug:
            layout.prop(context.window_manager, "enn_gp_move_vector")
            op = layout.operator(ENN_OT_move_gp.bl_idname)
            op.move_vector = context.window_manager.enn_gp_move_vector
            layout.prop(context.window_manager, "enn_gp_scale")
            op = layout.operator(ENN_OT_scale_gp.bl_idname)
            op.scale_vector = context.window_manager.enn_gp_scale
            layout.prop(context.window_manager, "enn_gp_rotate_angle")
            row = layout.row()
            op = row.operator(ENN_OT_rotate_gp.bl_idname)
            op.rotate_angle = context.window_manager.enn_gp_rotate_angle
            op = row.operator(ENN_OT_rotate_gp.bl_idname, text="Back")
            op.rotate_angle = -context.window_manager.enn_gp_rotate_angle


def register():
    from bpy.utils import register_class

    register_class(ENN_OT_toggle_gp_space)
    register_class(ENN_OT_add_gp)
    register_class(ENN_OT_remove_gp)
    register_class(ENN_OT_move_gp)
    register_class(ENN_OT_rotate_gp)
    register_class(ENN_OT_scale_gp)
    register_class(ENN_OT_gp_set_active_layer_color)
    register_class(ENN_PT_gn_edit_panel)


def unregister():
    from bpy.utils import unregister_class

    unregister_class(ENN_OT_move_gp)
    unregister_class(ENN_OT_rotate_gp)
    unregister_class(ENN_OT_scale_gp)
    unregister_class(ENN_OT_remove_gp)
    unregister_class(ENN_OT_add_gp)
    unregister_class(ENN_OT_toggle_gp_space)
    unregister_class(ENN_OT_gp_set_active_layer_color)
    unregister_class(ENN_PT_gn_edit_panel)
