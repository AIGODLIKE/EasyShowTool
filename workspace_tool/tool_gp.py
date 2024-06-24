import bpy
from ..public_path import get_tool_icon
from ..operator.ops_gp_modal import ENN_OT_gp_set_active_layer, ENN_OT_gp_drag_modal, ENN_OT_gp_set_active_layer_color
from ..operator.ops_gp_basic import ENN_OT_add_gp, ENN_OT_remove_gp, ENN_OT_scale_gp


# noinspection PyPep8Naming
class ENN_TL_gp_edit(bpy.types.WorkSpaceTool):
    bl_idname = "enn.gp_edit_tool"
    bL_idname_fallback = "node.select_box"
    bl_space_type = 'NODE_EDITOR'
    bl_context_mode = None
    bl_label = "Draw"
    bl_icon = get_tool_icon('gp_edit_tool')
    bl_keymap = (
        (ENN_OT_gp_set_active_layer.bl_idname,
         {"type": "LEFTMOUSE", "value": "CLICK"},
         {"properties": []},  # [("deselect_all", True)]
         ),
        (ENN_OT_add_gp.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK', "shift": True, "ctrl": False},
         {"properties": [('use_mouse_pos', True), ('add_type', 'TEXT')]}
         ),
        # normal mode drag
        (ENN_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False, "ctrl": False},
         {"properties": []}),
        # copy mode drag
        (ENN_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False, "ctrl": False, "alt": True},
         {"properties": []}),
        # delete
        (ENN_OT_remove_gp.bl_idname,
         {"type": 'X', "value": 'PRESS', "ctrl": False, "alt": False, "shift": False},
         {"properties": []}),
        # flip scale
        (ENN_OT_scale_gp.bl_idname,
         {"type": 'F', "value": 'PRESS', "ctrl": False, "alt": False, "shift": False},
         {"properties": [('scale_vector', (-1, 1))]}),
        (ENN_OT_scale_gp.bl_idname,
         {"type": 'F', "value": 'PRESS', "ctrl": False, "alt": False, "shift": True},
         {"properties": [('scale_vector', (1, -1))]}),
        # different enter event with drag
        (ENN_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "ctrl": False},
         {"properties": []}),
        (ENN_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False, "ctrl": True},
         {"properties": []}),
        (ENN_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "ctrl": True},
         {"properties": []}),

    )


class ENN_TL_gp_color(bpy.types.WorkSpaceTool):
    bl_idname = "enn.gp_color_tool"
    bL_idname_fallback = "node.select_box"
    bl_space_type = 'NODE_EDITOR'
    bl_context_mode = None
    bl_label = "Color"
    bl_icon = get_tool_icon('gp_color_tool')
    # bl_widget = "PH_GZG_place_tool"
    bl_keymap = (
        (ENN_OT_gp_set_active_layer_color.bl_idname,
         {"type": "LEFTMOUSE", "value": "CLICK"},
         {"properties": []},  # [("deselect_all", True)]
         ),
    )


def reigster():
    from bpy.utils import register_class, register_tool

    register_tool(ENN_TL_gp_edit, separator=True)
    register_tool(ENN_TL_gp_color, separator=False)


def unregister():
    from bpy.utils import unregister_class, unregister_tool

    unregister_tool(ENN_TL_gp_edit)
    unregister_tool(ENN_TL_gp_color)
