import bpy
from .functions import get_edit_tree_gp_data, has_edit_tree, is_valid_workspace_tool
from .op_palette_viewer import EST_PT_palette_viewer_active
from bpy.app.translations import pgettext_iface as _p


class EST_PT_active_layer(bpy.types.Panel):
    bl_idname = "EST_PT_active_layer"
    bl_label = ""
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_options = {'HEADER_LAYOUT_EXPAND'}
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and is_valid_workspace_tool(context) and get_edit_tree_gp_data(context)

    def draw_header(self, context):
        layout = self.layout
        layer_name = get_edit_tree_gp_data(context).layers.active.info
        layout.label(text=_p('Active') + ' : ' + layer_name, icon='GP_SELECT_STROKES')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        gp_data = get_edit_tree_gp_data(context)

        if not gp_data.layers: return
        col = layout.column(align=True)
        layer = gp_data.layers.active

        if not layer: return
        row = col.row(align=True)
        row.prop(layer, "color", text="Color")
        row.popover(panel=EST_PT_palette_viewer_active.bl_idname, text="Preset", icon='COLOR')
        col.prop(layer, "thickness", text="Thickness")
        col.prop(layer, "annotation_opacity", text="Opacity", slider=True)


def register():
    bpy.utils.register_class(EST_PT_active_layer)


def unregister():
    bpy.utils.unregister_class(EST_PT_active_layer)
