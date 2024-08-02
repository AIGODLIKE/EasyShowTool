import bpy

from bpy.props import PointerProperty, IntProperty, EnumProperty, StringProperty, FloatVectorProperty, FloatProperty

from ..model.model_color import ColorPaletteModel
from ..model.data_enums import ShootAngles, GPAddTypes
from ..view_model.view_model_select import SelectedGPLayersRuntime
from ..model.model_gp import BuildGreasePencilData
from ..bl_operator.functions import has_edit_tree, get_edit_tree_gp_data


def poll_gp_data(context) -> bpy.types.GreasePencil | None:
    return context.space_data.edit_tree.grease_pencil if has_edit_tree(context) else None


def update_selected_layers_color(self, context):
    if not (gp_data := poll_gp_data(context)): return

    with BuildGreasePencilData(gp_data) as gp_data_builder:
        for layer_name in SelectedGPLayersRuntime.selected_layers():
            gp_data_builder.color(layer_name, self.est_palette_color)


def update_selected_layers_thickness(self, context):
    if not (gp_data := poll_gp_data(context)): return

    with BuildGreasePencilData(gp_data) as gp_data_builder:
        for layer_name in SelectedGPLayersRuntime.selected_layers():
            gp_data_builder.thickness(layer_name, self.est_gp_thickness)


def update_selected_layers_opacity(self, context):
    if not (gp_data := poll_gp_data(context)): return
    with BuildGreasePencilData(gp_data) as gp_data_builder:
        for layer_name in SelectedGPLayersRuntime.selected_layers():
            gp_data_builder.opacity(layer_name, self.est_gp_opacity)


def register():
    ColorPaletteModel.register_color_icon()

    bpy.types.Scene.est_palette_color = FloatVectorProperty(name="Color", size=3, subtype='COLOR_GAMMA', min=0.0,
                                                            max=1.0,
                                                            default=(0.8, 0.8, 0.8),
                                                            update=update_selected_layers_color)
    bpy.types.Scene.est_gp_opacity = FloatProperty(name="Opacity", default=1.0, min=0.0, max=1.0,
                                                   update=update_selected_layers_opacity)
    bpy.types.Scene.est_gp_thickness = IntProperty(name="Thickness", default=1, min=1, max=10,
                                                   update=update_selected_layers_thickness)

    # Grease Pencil Add
    bpy.types.Scene.est_gp_size = IntProperty(name="Size", default=500, soft_min=200, soft_max=2000)
    bpy.types.Scene.est_gp_add_type = EnumProperty(items=lambda _, __: GPAddTypes.enum_items())
    bpy.types.Scene.est_gp_text = StringProperty(name="Text", default="Hello World")
    bpy.types.Scene.est_gp_text_font = PointerProperty(type=bpy.types.VectorFont)
    bpy.types.Scene.est_gp_obj = PointerProperty(name='Object', type=bpy.types.Object,
                                                 poll=lambda self, obj: obj.type in {'MESH', 'GPENCIL'})
    bpy.types.Scene.est_gp_obj_shot_angle = EnumProperty(name="Shot Orientation",
                                                         items=lambda _, __: ShootAngles.enum_items())
    bpy.types.Scene.est_gp_icon = StringProperty(name="Icon", default="BLENDER")


def unregister():
    ColorPaletteModel.unregister_color_icon()

    del bpy.types.Scene.est_gp_size
    del bpy.types.Scene.est_gp_add_type
    del bpy.types.Scene.est_gp_text
    del bpy.types.Scene.est_gp_obj
    del bpy.types.Scene.est_gp_obj_shot_angle
    del bpy.types.Scene.est_gp_icon
    del bpy.types.Scene.est_palette_color
    del bpy.types.Scene.est_gp_opacity
    del bpy.types.Scene.est_gp_thickness
