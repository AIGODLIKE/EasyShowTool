import bpy
from bpy.props import StringProperty, IntProperty, PointerProperty, FloatVectorProperty

from .gp_utils import CreateGreasePencilData as gpd_create
from .gp_utils import BuildGreasePencilData as gpd_build
from .ops_notes import has_edit_tree


def enum_add_type_items() -> list[tuple[str, str, str]]:
    """Return the items for the add_type enum property."""
    data: dict = {
        'TEXT': "Text",
        'MESH': "Mesh Object",
    }
    return [(key, value, "") for key, value in data.items()]


class ENN_OT_add_gp(bpy.types.Operator):
    bl_idname = "enn.add_gp"
    bl_label = "Add"
    bl_options = {'UNDO'}

    add_type: bpy.props.EnumProperty(
        items=lambda self, context: enum_add_type_items(),
    )

    text: StringProperty(name="Text", default="Hello World")
    size: IntProperty(name="Size", default=100)
    obj: StringProperty(name="Object", default="")

    location: FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        font_gp_data: bpy.types.GreasePencil = None

        if not gp_data:
            gp_data = gpd_create.empty()

        if self.add_type == 'MESH':
            obj = bpy.data.objects.get(self.obj, None)
            if not obj:
                return {'CANCELLED'}
            if obj.type == 'MESH':
                font_gp_data = gpd_create.from_mesh_obj(obj)
            elif obj.type == 'GPENCIL':
                font_gp_data = gpd_create.from_gp_obj(obj)
            else:
                return {'CANCELLED'}
        elif self.add_type == 'TEXT':
            font_gp_data = gpd_create.from_text(self.text, self.size)

        if not font_gp_data: return {'CANCELLED'}

        with gpd_build(gp_data) as gp_data_builder:
            gp_data_builder.link(context).join(font_gp_data).move(-1, self.location).color(-1, '#E7E7E7').to_2d()
        return {'FINISHED'}


class ENN_OT_add_gp_modal(bpy.types.Operator):
    bl_idname = "enn.add_gp_modal"
    bl_label = "Add"
    bl_description = "Add Grease from %s"
    bl_options = {'UNDO'}

    add_type: bpy.props.EnumProperty(
        items=lambda self, context: enum_add_type_items(),
    )

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    @classmethod
    def description(cls, context, property):
        return cls.bl_description % cls.add_type

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        context.window.cursor_set('PICK_AREA')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE':
            context.window.cursor_modal_restore()
            ui_scale = context.preferences.system.ui_scale
            x, y = context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)
            location = x / ui_scale, y / ui_scale
            self._add(context, location)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def _add(self, context, location):
        if self.add_type == 'TEXT':
            bpy.ops.enn.add_gp('EXEC_DEFAULT',
                               add_type='TEXT',
                               text=context.window_manager.enn_gp_text,
                               size=context.window_manager.enn_gp_size,
                               location=location)
        elif self.add_type == 'MESH':
            bpy.ops.enn.add_gp('EXEC_DEFAULT',
                               add_type='MESH',
                               size=context.window_manager.enn_gp_size,
                               obj=context.window_manager.enn_gp_obj.name,
                               location=location)


class ENN_PT_gn_edit_panel(bpy.types.Panel):
    bl_label = "Edit Grease Pencil Text"
    bl_idname = "ENN_PT_gn_edit_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.window_manager, "enn_gp_size")

        layout.prop(context.window_manager, "enn_gp_add_type")

        layout.separator()
        layout.prop(context.window_manager, "enn_gp_text")
        op = layout.operator(ENN_OT_add_gp_modal.bl_idname)
        op.add_type = 'TEXT'

        layout.prop(context.window_manager, "enn_gp_obj")
        op = layout.operator(ENN_OT_add_gp_modal.bl_idname)
        op.add_type = 'MESH'


def header_menu(self, context):
    layout = self.layout
    layout.operator(ENN_OT_add_gp_modal.bl_idname, icon='FONT_DATA')


def register():
    bpy.types.WindowManager.enn_gp_size = bpy.props.IntProperty(name="Pixel Size", default=100)
    bpy.types.WindowManager.enn_gp_add_type = bpy.props.EnumProperty(items=lambda self, context: enum_add_type_items())
    bpy.types.WindowManager.enn_gp_text = bpy.props.StringProperty(name="Text", default="Hello World")
    bpy.types.WindowManager.enn_gp_obj = bpy.props.PointerProperty(type=bpy.types.Object,
                                                                   poll=lambda self, obj: obj.type in {'MESH',
                                                                                                       'GPENCIL'})

    bpy.utils.register_class(ENN_OT_add_gp)
    bpy.utils.register_class(ENN_OT_add_gp_modal)
    bpy.utils.register_class(ENN_PT_gn_edit_panel)
    # bpy.types.NODE_HT_header.append(header_menu)


def unregister():
    bpy.utils.unregister_class(ENN_OT_add_gp)
    bpy.utils.unregister_class(ENN_OT_add_gp_modal)
    bpy.utils.unregister_class(ENN_PT_gn_edit_panel)
    # bpy.types.NODE_HT_header.remove(header_menu)
