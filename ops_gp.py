import bpy

from .gp_utils import GreasePencilDataFactory, GreasePencilDataBuilder
from .ops_notes import has_edit_tree


class ENN_OT_add_gp_text(bpy.types.Operator):
    bl_idname = "enn.add_gp_text"
    bl_label = "Add Text"
    bl_description = "Add Grease Pencil Text"
    bl_options = {'UNDO'}

    text: bpy.props.StringProperty(name="Text", default="Hello World")
    size: bpy.props.IntProperty(name="Size", default=100)

    location: bpy.props.FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil

        if not gp_data:
            gp_data = GreasePencilDataFactory.empty()
        font_gp_data = GreasePencilDataFactory.from_text(self.text, self.size)

        with GreasePencilDataBuilder(gp_data) as gp_data_builder:
            gp_data_builder.link(context).join(font_gp_data).move(-1, self.location)

        GreasePencilDataFactory.cleanup()
        return {'FINISHED'}


class ENN_OT_add_gp_text_modal(bpy.types.Operator):
    bl_idname = "enn.add_gp_text_modal"
    bl_label = "Add Text"
    bl_description = "Add Grease Pencil Text"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        context.window.cursor_set('MOVE_X')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE':
            context.window.cursor_set('DEFAULT')
            ui_scale = context.preferences.system.ui_scale
            x, y = context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
            location = x / ui_scale, y / ui_scale
            print(location)
            bpy.ops.enn.add_gp_text('EXEC_DEFAULT',
                                    text=context.window_manager.enn_gp_text,
                                    size=context.window_manager.enn_gp_text_size,
                                    location=location)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}


class ENN_PT_gn_edit_panel(bpy.types.Panel):
    bl_label = "Edit Grease Pencil Text"
    bl_idname = "ENN_PT_gn_edit_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.window_manager, "enn_gp_text")
        layout.prop(context.window_manager, "enn_gp_text_size")
        layout.operator(ENN_OT_add_gp_text_modal.bl_idname)


def header_menu(self, context):
    layout = self.layout
    layout.operator(ENN_OT_add_gp_text_modal.bl_idname, icon='FONT_DATA')


def register():
    bpy.types.WindowManager.enn_gp_text = bpy.props.StringProperty(name="Text", default="Hello World")
    bpy.types.WindowManager.enn_gp_text_size = bpy.props.IntProperty(name="Size", default=100)

    bpy.utils.register_class(ENN_OT_add_gp_text)
    bpy.utils.register_class(ENN_OT_add_gp_text_modal)
    bpy.utils.register_class(ENN_PT_gn_edit_panel)
    bpy.types.NODE_HT_header.append(header_menu)


def unregister():
    bpy.utils.unregister_class(ENN_OT_add_gp_text)
    bpy.utils.unregister_class(ENN_OT_add_gp_text_modal)
    bpy.utils.unregister_class(ENN_PT_gn_edit_panel)
    bpy.types.NODE_HT_header.remove(header_menu)
