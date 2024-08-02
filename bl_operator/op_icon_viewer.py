import bpy
import re
from bpy.props import StringProperty
from .functions import get_icons, has_edit_tree, is_valid_workspace_tool

ICONS = []


class EST_OT_set_icon(bpy.types.Operator):
    bl_idname = "est.set_icon"
    bl_label = "Set Icon"
    bl_description = "Set the icon"
    bl_options = {'UNDO'}

    icon: StringProperty()

    def execute(self, context):
        context.scene.est_gp_icon = self.icon
        context.area.tag_redraw()
        return {'FINISHED'}


class EST_PT_icon_viewer(bpy.types.Panel):
    bl_idname = "EST_PT_icon_viewer"
    bl_label = ""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_options = {'HEADER_LAYOUT_EXPAND'}
    bl_order = 3

    @classmethod
    def poll(cls, context):
        global ICONS
        if not ICONS:
            ICONS = get_icons()
        return has_edit_tree(context) and is_valid_workspace_tool(
            context) and context.scene.est_gp_add_type == 'BL_ICON'

    def draw_header(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(context.window_manager, 'est_gp_icon_filter', text='', icon='VIEWZOOM')
        row.separator()

    def draw(self, context):
        layout = self.layout
        filter: str = context.window_manager.est_gp_icon_filter

        col = layout.box().column(align=True)
        gird = col.grid_flow(row_major=True, columns=8, even_columns=True, even_rows=True, align=True)
        for icon in ICONS:
            if filter and not re.search(filter, str(icon), re.I):
                continue
            gird.operator("est.set_icon", text='', icon=icon, emboss=False).icon = icon


def register():
    bpy.utils.register_class(EST_OT_set_icon)
    bpy.utils.register_class(EST_PT_icon_viewer)


def unregister():
    bpy.utils.unregister_class(EST_OT_set_icon)
    bpy.utils.unregister_class(EST_PT_icon_viewer)
