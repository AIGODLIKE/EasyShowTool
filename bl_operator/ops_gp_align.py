import bpy
from bpy.props import EnumProperty
from ..model.model_gp_bbox import GPencilLayersBBox, GPencilLayerBBox
from ..model.model_gp import BuildGreasePencilData
from .functions import get_edit_tree_gp_data, has_edit_tree
from ..view_model.view_model_select import SelectedGPLayersRuntime
from ..model.data_enums import AlignMode


class EST_OT_align_gp(bpy.types.Operator):
    bl_idname = "est.align_gp"
    bl_label = "Align"
    bl_description = "Align the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    align_mode: EnumProperty(
        name='Align Mode',
        items=lambda _, __: AlignMode.enum_items()
    )

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and get_edit_tree_gp_data(context) and SelectedGPLayersRuntime.selected_layers()

    def execute(self, context):
        gp_data = get_edit_tree_gp_data(context)
        bboxs = GPencilLayersBBox(gp_data)
        diff = bboxs.calc_layers_edge_difference(SelectedGPLayersRuntime.selected_layers(), mode=self.align_mode)
        print(diff)
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            for layer_name, diff_vector in diff.items():
                gp_data_builder.move(layer_name, -diff_vector)

        return {'FINISHED'}


class EST_OT_align_menu(bpy.types.Menu):
    bl_idname = "EST_OT_align_menu"
    bl_label = "Align"

    def draw(self, context):
        layout = self.layout
        for mode in AlignMode:
            layout.operator(EST_OT_align_gp.bl_idname, text=mode.value).align_mode = mode.name


def register():
    bpy.utils.register_class(EST_OT_align_gp)
    bpy.utils.register_class(EST_OT_align_menu)


def unregister():
    bpy.utils.unregister_class(EST_OT_align_gp)
    bpy.utils.unregister_class(EST_OT_align_menu)
