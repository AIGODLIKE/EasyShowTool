import bpy
from ..public_path import get_tool_icon
from ..bl_operator.ops_gp_modal import EST_OT_gp_set_active_layer, EST_OT_gp_drag_modal, EST_OT_add_gp_modal,EST_OT_move_gp_modal
from ..bl_operator.ops_gp_basic import EST_OT_remove_gp, EST_OT_scale_gp, \
    EST_OT_gp_set_active_layer_color


class EST_TL_gp_add(bpy.types.WorkSpaceTool):
    bl_idname = "est.gp_add_tool"
    bL_idname_fallback = "node.select_box"
    bl_space_type = 'NODE_EDITOR'
    bl_context_mode = None
    bl_label = "Add"
    bl_icon = get_tool_icon('gp_add_tool')
    bl_keymap = (
        (EST_OT_add_gp_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'PRESS', "shift": False, "ctrl": False},
         # {"properties": [('use_mouse_pos', True)]}
         {"properties": []}
         ),
    )


# noinspection PyPep8Naming
class EST_TL_gp_edit(bpy.types.WorkSpaceTool):
    bl_idname = "est.gp_edit_tool"
    bL_idname_fallback = "node.select_box"
    bl_space_type = 'NODE_EDITOR'
    bl_context_mode = None
    bl_label = "Move"
    bl_icon = get_tool_icon('gp_edit_tool')
    bl_keymap = (
        # GSR
        (EST_OT_move_gp_modal.bl_idname,
         {"type": 'G', "value": 'PRESS', "shift": False, "ctrl": False},
         {"properties": []}),
        # add
        (EST_OT_gp_set_active_layer.bl_idname,
         {"type": "LEFTMOUSE", "value": "CLICK"},
         {"properties": []},  # [("deselect_all", True)]
         ),
        (EST_OT_add_gp_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'DOUBLE_CLICK', "shift": False, "ctrl": False},
         # {"properties": [('use_mouse_pos', True)]}
         {"properties": []}
         ),
        (EST_OT_gp_set_active_layer_color.bl_idname,
         {"type": "C", "value": "PRESS"},
         {"properties": []},  # [("deselect_all", True)]
         ),
        # normal mode drag
        (EST_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False, "ctrl": False},
         {"properties": []}),
        # copy mode drag
        (EST_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False, "ctrl": False, "alt": True},
         {"properties": []}),
        # different enter event with drag
        (EST_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "ctrl": False},
         {"properties": []}),
        (EST_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False, "ctrl": True},
         {"properties": []}),
        (EST_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True, "ctrl": True},
         {"properties": []}),
        # delete
        (EST_OT_remove_gp.bl_idname,
         {"type": 'X', "value": 'PRESS', "ctrl": False, "alt": False, "shift": False},
         {"properties": []}),
        # flip scale
        (EST_OT_scale_gp.bl_idname,
         {"type": 'F', "value": 'PRESS', "ctrl": False, "alt": False, "shift": False},
         {"properties": [('scale_vector', (-1, 1))]}),
        (EST_OT_scale_gp.bl_idname,
         {"type": 'F', "value": 'PRESS', "ctrl": False, "alt": False, "shift": True},
         {"properties": [('scale_vector', (1, -1))]}),
    )

    def draw_settings(self, layout, tool):
        scene = bpy.context.scene
        row = layout.row()
        row.prop(scene, 'est_gp_transform_mode', text="Transform Orientations", expand=True)

        box = layout.box()
        box.label(text="New", icon='ADD')
        row = box.row()
        row.prop(scene, "est_gp_add_type", text='Source', expand=True)
        box.prop(scene, "est_gp_size")
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(scene, 'est_palette_color', text='Color')
        row.popover(panel='EST_PT_palette_viewer', text='Preset', icon='COLOR')
        col.prop(scene, "est_gp_opacity",slider=True)
        col.prop(scene, "est_gp_thickness",slider=True)


        if scene.est_gp_add_type == 'TEXT':
            box.template_ID(scene, "est_gp_text_font", open="font.open", unlink="font.unlink")
            box.prop(scene, "est_gp_text")
        elif scene.est_gp_add_type == 'OBJECT':
            box.prop(scene, "est_gp_obj")
            box.prop(scene, "est_gp_obj_shot_angle")
        elif scene.est_gp_add_type == 'BL_ICON':
            row = box.row()
            row.alignment = 'RIGHT'
            row.label(text=bpy.context.scene.est_gp_icon, icon=bpy.context.scene.est_gp_icon)


class EST_TL_gp_color(bpy.types.WorkSpaceTool):
    bl_idname = "est.gp_color_tool"
    bL_idname_fallback = "node.select_box"
    bl_space_type = 'NODE_EDITOR'
    bl_context_mode = None
    bl_label = "Color"
    bl_icon = get_tool_icon('gp_color_tool')
    # bl_widget = "PH_GZG_place_tool"
    bl_keymap = (
        (EST_OT_gp_set_active_layer_color.bl_idname,
         {"type": "LEFTMOUSE", "value": "CLICK"},
         {"properties": []},  # [("deselect_all", True)]
         ),
    )


def reigster():
    from bpy.utils import register_tool

    # register_tool(EST_TL_gp_add, separator=True)
    register_tool(EST_TL_gp_edit, separator=True)
    # register_tool(EST_TL_gp_color, separator=False)


def unregister():
    from bpy.utils import unregister_tool

    # unregister_tool(EST_TL_gp_add)
    unregister_tool(EST_TL_gp_edit)
    # unregister_tool(EST_TL_gp_color)
