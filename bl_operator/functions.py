import contextlib
import os
from typing import Optional, Union, Sequence
from mathutils import Vector
import bpy
from contextlib import contextmanager

from ..model.utils import ShootAngles
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


def get_edit_tree_gp_data(context: bpy.types.Context) -> Union[bpy.types.GreasePencil, None]:
    """Check if there is an active grease pencil data on the active node tree."""
    nt: bpy.types.NodeTree = context.space_data.edit_tree
    gp_data: bpy.types.GreasePencil = nt.grease_pencil
    if not gp_data:
        return None
    return gp_data


def is_valid_workspace_tool(context) -> bool:
    return context.workspace.tools.from_space_node().idname in {'est.gp_edit_tool', 'est.gp_color_tool'}


def enum_add_type_items() -> list[tuple[str, str, str]]:
    """Return the items for the add_type enum property."""
    data: dict = {
        'TEXT': "Text",
        'OBJECT': "Object",
        'BL_ICON': "Icon",
    }
    return [(key, value, "") for key, value in data.items()]


def enum_shot_orient_items() -> list[tuple[str, str, str]]:
    """Return the items for the shot_orient enum property."""
    return [(euler.name, euler.name.replace('_', ' ').title(), '') for euler in ShootAngles]


def get_pos_layer_index(gp_data: bpy.types.GreasePencil, pos: Union[Sequence, Vector], feather=0) -> Union[int, None]:
    """get the layer index by the mouse position."""
    # TODO select through if some layers are overlapped
    try:
        bboxs: list[GPencilLayerBBox] = [GPencilLayerBBox(gp_data, layer) for layer in
                                         gp_data.layers]
        mouse_detect = MouseDetectModel()
        for i, bbox in enumerate(bboxs):
            bbox.calc_bbox(i)
            mouse_detect.bind_bbox(bbox)
            if mouse_detect.in_area(pos, feather):
                return bbox.last_layer_index
    except ReferenceError:  # ctrl z will cause the reference error
        return None
    except AttributeError:  # switch to other tool will cause the attribute error
        return None
    return None


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


def load_icon_svg(icon: str) -> Union[bpy.types.Object, None]:
    SCALE = 2

    if (icon_svg := get_svg_icon(icon.lower())) is None:
        return None
    with ensure_3d_view(bpy.context):  # the svg import operator need a 3d view to work(Strange)
        bpy.ops.wm.gpencil_import_svg(filepath=icon_svg, scale=SCALE)

    return bpy.context.object
