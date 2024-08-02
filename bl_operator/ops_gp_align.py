import bpy
from typing import ClassVar
from dataclasses import dataclass, field
from pathlib import Path

from bpy.props import EnumProperty
from ..model.model_gp_bbox import GPencilLayersBBox, GPencilLayerBBox
from ..model.model_gp import BuildGreasePencilData
from .functions import get_edit_tree_gp_data, has_edit_tree
from ..view_model.view_model_select import SelectedGPLayersRuntime
from ..model.data_enums import AlignMode, DistributionMode
from ..public_path import get_png_icons_directory


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


@dataclass
class AlignIcon:
    paths: ClassVar[list[Path]] = []
    pv_coll: ClassVar[dict] = {}
    icon_id: ClassVar[dict[str, int]] = {}

    @classmethod
    def get_icon_id(cls, name: str) -> int:
        return cls.icon_id.get(name)

    @classmethod
    def register_icon(cls):
        if bpy.app.background: return

        d = get_png_icons_directory()
        cls.paths.extend([fp for fp in d.iterdir()])

        from bpy.utils import previews
        pcoll = previews.new()
        for icon_path in cls.paths:
            if icon_path.stem in pcoll:
                continue
            pcoll.load(icon_path.stem, icon_path.as_posix(), 'IMAGE')
            cls.icon_id[icon_path.stem] = pcoll.get(icon_path.stem).icon_id
        cls.pv_coll['est_align_pv'] = pcoll

        # print('PATHS!!!!!!!!!!!!', cls.paths)
        # print("ICON!!!!!!!!!!!!", cls.icon_id)

    @classmethod
    def unregister_icon(cls):
        if bpy.app.background: return

        from bpy.utils import previews
        for pcoll in cls.pv_coll.values():
            previews.remove(pcoll)
        cls.pv_coll.clear()


class EST_MT_align_menu(bpy.types.Menu):
    bl_idname = "EST_MT_align_menu"
    bl_label = "Align"

    def draw(self, context):
        layout = self.layout
        self.draw_layout(context, layout)

    def draw_layout(self, context, layout, text: bool = True):
        for mode in AlignMode:
            op = layout.operator(EST_OT_align_gp.bl_idname,
                                 text=f'Align {mode.value}' if text else '',
                                 icon_value=AlignIcon.get_icon_id(f'Align{mode.value}'))
            op.align_mode = mode.name


class EST_MT_distribution_menu(bpy.types.Menu):
    bl_idname = "EST_MT_distribution_menu"
    bl_label = "Distribution"

    def draw(self, context):
        layout = self.layout
        self.draw_layout(context, layout)

    def draw_layout(self, context, layout, text: bool = True):
        for mode in DistributionMode:
            op = layout.operator(EST_OT_distribution_gp.bl_idname,
                                 text=f'Distribute {mode.value}' if text else '',
                                 icon_value=AlignIcon.get_icon_id(f'Distribution{mode.value}'))
            op.distribution_mode = mode.name


def register():
    AlignIcon.register_icon()

    bpy.utils.register_class(EST_OT_align_gp)
    bpy.utils.register_class(EST_MT_align_menu)
    bpy.utils.register_class(EST_OT_distribution_gp)
    bpy.utils.register_class(EST_MT_distribution_menu)


def unregister():
    bpy.utils.unregister_class(EST_OT_align_gp)
    bpy.utils.unregister_class(EST_MT_align_menu)
    bpy.utils.unregister_class(EST_OT_distribution_gp)
    bpy.utils.unregister_class(EST_MT_distribution_menu)

    AlignIcon.unregister_icon()
