import bpy
from bpy.props import EnumProperty
from ..model.model_gp_bbox import GPencilLayersBBox, GPencilLayerBBox
from ..model.model_gp import BuildGreasePencilData
from .functions import get_edit_tree_gp_data, has_edit_tree
from ..view_model.view_model_select import SelectedGPLayersRuntime
from ..model.data_enums import AlignMode, DistributionMode


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
        diff = bboxs.calc_layers_edge_difference(SelectedGPLayersRuntime.selected_layers(),
                                                 mode=getattr(AlignMode, self.align_mode))
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            for layer_name, diff_vector in diff.items():
                gp_data_builder.move(layer_name, -diff_vector)
        SelectedGPLayersRuntime.update_from_gp_data(gp_data)
        return {'FINISHED'}


class EST_OT_distribution_gp(bpy.types.Operator):
    bl_idname = "est.distribution_gp"
    bl_label = "Distribution"
    bl_description = "Distribute the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    distribution_mode: EnumProperty(
        name='Distribution Mode',
        items=lambda _, __: DistributionMode.enum_items()
    )

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and get_edit_tree_gp_data(context) and SelectedGPLayersRuntime.selected_layers()

    def execute(self, context):
        gp_data = get_edit_tree_gp_data(context)
        bboxs = GPencilLayersBBox(gp_data)
        diff = bboxs.calc_layers_distribute_difference(SelectedGPLayersRuntime.selected_layers(),
                                                 mode=getattr(DistributionMode, self.distribution_mode))
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            for layer_name, diff_vector in diff.items():
                gp_data_builder.move(layer_name, diff_vector)
        SelectedGPLayersRuntime.update_from_gp_data(gp_data)
        return {'FINISHED'}


class EST_OT_align_menu(bpy.types.Menu):
    bl_idname = "EST_OT_align_menu"
    bl_label = "Align"

    def draw(self, context):
        layout = self.layout
        for mode in AlignMode:
            layout.operator(EST_OT_align_gp.bl_idname, text=mode.value).align_mode = mode.name


class EST_OT_distribution_menu(bpy.types.Menu):
    bl_idname = "EST_OT_distribution_menu"
    bl_label = "Distribution"

    def draw(self, context):
        layout = self.layout
        for mode in DistributionMode:
            layout.operator(EST_OT_distribution_gp.bl_idname, text=mode.value).distribution_mode = mode.name


def register():
    bpy.utils.register_class(EST_OT_align_gp)
    bpy.utils.register_class(EST_OT_align_menu)
    bpy.utils.register_class(EST_OT_distribution_gp)
    bpy.utils.register_class(EST_OT_distribution_menu)


def unregister():
    bpy.utils.unregister_class(EST_OT_align_gp)
    bpy.utils.unregister_class(EST_OT_align_menu)
    bpy.utils.unregister_class(EST_OT_distribution_gp)
    bpy.utils.unregister_class(EST_OT_distribution_menu)
