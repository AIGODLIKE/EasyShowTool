from typing import Optional

import bpy
from ..model.utils import ShootAngles

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
    if context.space_data.edit_tree.nodes.active is None:
        return False
    if bl_idname:
        if context.space_data.edit_tree.nodes.active.bl_idname != bl_idname:
            return False
    return True


def is_valid_workspace_tool(context) -> bool:
    return context.workspace.tools.from_space_node().idname in {'enn.gp_edit_tool','enn.gp_color_tool'}


def enum_add_type_items() -> list[tuple[str, str, str]]:
    """Return the items for the add_type enum property."""
    data: dict = {
        'TEXT': "Text",
        'OBJECT': "Object",
    }
    return [(key, value, "") for key, value in data.items()]


def enum_shot_orient_items() -> list[tuple[str, str, str]]:
    """Return the items for the shot_orient enum property."""
    return [(euler.name, euler.name.replace('_', ' ').title(), '') for euler in ShootAngles]
