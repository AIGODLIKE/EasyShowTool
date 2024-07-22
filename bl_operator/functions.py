import contextlib
import os
from typing import Optional, Union, Sequence
from mathutils import Vector
import bpy
from contextlib import contextmanager

from ..model.data_enums import ShootAngles
from ..model.model_gp_bbox import GPencilLayerBBox
from ..view_model.view_model_detect import MouseDetectModel
from ..public_path import get_svg_icon


def tag_redraw():
    for area in bpy.context.screen.areas:
        area.tag_redraw()


def has_edit_tree(context: bpy.types.Context) -> bool:
    if context.area.type != 'NODE_EDITOR':
        return False
    if context.space_data.edit_tree is None:
        return False
    return True


def has_active_node(context: bpy.types.Context, bl_idname: Optional[str] = None) -> bool:
    """Check if there is an active node in the active node tree."""
    if context.space_data.edit_tree.nodes.active is None:
        return False
    if bl_idname:
        if context.space_data.edit_tree.nodes.active.bl_idname != bl_idname:
            return False
    return True


def get_edit_tree_gp_data(context: bpy.types.Context) -> bpy.types.GreasePencil | None:
    """Check if there is an active grease pencil data on the active node tree."""
    nt: bpy.types.NodeTree = context.space_data.edit_tree
    gp_data: bpy.types.GreasePencil = nt.grease_pencil
    if not gp_data:
        return None
    return gp_data


def is_valid_workspace_tool(context) -> bool:
    return context.workspace.tools.from_space_node().idname in {'est.gp_edit_tool', 'est.gp_color_tool'}


def get_pos_layer_index(gp_data: bpy.types.GreasePencil, pos: Sequence | Vector, feather=0,
                        local: bool = True) -> int | None:
    """get the layer index by the mouse position."""
    # TODO select through if some layers are overlapped
    try:
        bbox = GPencilLayerBBox(gp_data)
        bbox.mode = 'LOCAL' if local else 'GLOBAL'
        mouse_detect = MouseDetectModel()
        mouse_detect.bind_bbox(bbox)

        for i, layer in enumerate(gp_data.layers):
            bbox.calc_bbox(i)
            if mouse_detect.in_bbox_area(pos, feather):
                if gp_data.layers.active_index == i:
                    continue
                return bbox.last_layer_index
    except ReferenceError:  # ctrl z will cause the reference error
        return None
    except AttributeError:  # switch to other tool will cause the attribute error
        return None
    return None


def ensure_builtin_font():
    """if a old file is loaded, the font may not be loaded, so load the built-in font."""
    if bpy.context.scene.est_gp_text_font is None and 'Bfont Regular' not in bpy.data.fonts:
        bpy.data.curves.new('tmp', type='FONT')  # make sure the built-in font is loaded
        bpy.context.scene.est_gp_text_font = bpy.data.fonts['Bfont Regular']


@contextmanager
def ensure_3d_view(context: bpy.types.Context):
    ori_ui_type = context.area.type
    context.area.type = 'VIEW_3D'
    yield
    context.area.type = ori_ui_type


def get_icons() -> list[str]:
    """Return the list of built-in icons."""
    icons: list[str] = [icon for icon in
                        bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys()
                        if icon != 'NONE' and  # skip the NONE icon
                        'BLANK' not in icon and  # skip the blank icons
                        'COLORSET_' not in icon and  # skip the color set icons
                        'BRUSH_DATA_' not in icon and  # skip the brush data icons
                        'EVENT_' not in icon  # skip the event icons
                        ]
    icons = [icon for icon in icons if icon.lower() + '.svg' in os.listdir(get_svg_icon())]
    return icons


def load_icon_svg(icon: str) -> bpy.types.Object | None:
    SCALE = 2

    if (icon_svg := get_svg_icon(icon.lower())) is None:
        return None
    with ensure_3d_view(bpy.context):  # the svg import operator need a 3d view to work(Strange)
        bpy.ops.wm.gpencil_import_svg(filepath=icon_svg, scale=SCALE)

    return bpy.context.object
