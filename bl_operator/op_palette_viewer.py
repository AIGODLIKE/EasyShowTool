import bpy
import re
from bpy.props import StringProperty
from ..model.model_color import ColorPaletteModel
from ..public_path import get_color_palettes
from .functions import get_icons, has_edit_tree, is_valid_workspace_tool
from ..model.utils import ColorTool

ICONS = []


class EST_OT_set_color(bpy.types.Operator):
    bl_idname = "est.color"
    bl_label = "Set Color"
    bl_options = {'UNDO'}

    hex: StringProperty()

    def execute(self, context):
        context.scene.est_palette_color = ColorTool.hex_2_rgb(self.hex)
        return {'FINISHED'}


class EST_PT_palette_viewer(bpy.types.Panel):
    bl_idname = "EST_PT_palette_viewer"
    bl_label = "Color Palette"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_options = {'HEADER_LAYOUT_EXPAND'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and is_valid_workspace_tool(context)

    # def draw_header(self, context):
    #     layout = self.layout
    #     row = layout.row(align=True)
    #     row.prop(context.window_manager, 'est_gp_icon_filter', text='', icon='VIEWZOOM')
    #     row.separator()

    def draw(self, context):
        layout = self.layout
        colors: dict[str, list[str]] = get_color_palettes()
        # sort_dir, 'SocketColor' first
        for directory, color_list in colors.items():
            col = layout.box().column(align=True)
            col.label(text=directory, icon='COLOR')
            row = col.row(align=True)
            row.alignment = 'CENTER'
            gird = row.grid_flow(row_major=False, even_columns=True, even_rows=True, align=True)
            gird.scale_x= 0.65
            for color in color_list:
                gird.operator("est.color", text='', icon_value=ColorPaletteModel.get_color_icon_id(color),
                              emboss=False).hex = color


def register():
    bpy.utils.register_class(EST_OT_set_color)
    bpy.utils.register_class(EST_PT_palette_viewer)


def unregister():
    bpy.utils.unregister_class(EST_OT_set_color)
    bpy.utils.unregister_class(EST_PT_palette_viewer)
