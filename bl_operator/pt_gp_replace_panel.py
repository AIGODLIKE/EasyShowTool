import bpy.types
from bpy.app.translations import pgettext_iface as iface_
from .ops_gp_basic import EST_OT_remove_gp

OLD_DRAW = None


def draw(self, context):
    layout = self.layout
    layout.use_property_decorate = False
    space = context.space_data

    is_clip_editor = space.type == 'CLIP_EDITOR'

    # Grease Pencil owner.
    gpd_owner = context.annotation_data_owner
    gpd = context.annotation_data

    # Owner selector.
    if is_clip_editor:
        col = layout.column()
        col.label(text="Data Source:")
        row = col.row()
        row.prop(space, "annotation_source", expand=True)

    # Only allow adding annotation ID if its owner exist
    if context.annotation_data_owner is None:
        row = layout.row()
        row.active = False
        row.label(text="No annotation source")
        return

    row = layout.row()
    row.template_ID(gpd_owner, "grease_pencil", new="gpencil.annotation_add", unlink="gpencil.data_unlink")

    # List of layers/notes.
    if gpd and gpd.layers:
        draw_layers(context, layout, gpd)


def draw_layers(context, layout, gpd):
    row = layout.row()

    col = row.column()
    if len(gpd.layers) >= 2:
        layer_rows = 5
    else:
        layer_rows = 3
    col.template_list(
        "GPENCIL_UL_annotation_layer", "", gpd, "layers", gpd.layers, "active_index",
        rows=layer_rows, sort_reverse=True, sort_lock=True,
    )

    col = row.column()

    sub = col.column(align=True)
    sub.operator("gpencil.layer_annotation_add", icon='ADD', text="")
    if context.space_data.type != 'NODE_EDITOR':
        sub.operator("gpencil.layer_annotation_remove", icon='REMOVE', text="")
    else:
        # change this to custom delete
        sub.operator(EST_OT_remove_gp.bl_idname, icon='REMOVE', text="").delete_active_only = True

    gpl = context.active_annotation_layer
    if gpl:
        if len(gpd.layers) > 1:
            col.separator()

            sub = col.column(align=True)
            sub.operator("gpencil.layer_annotation_move", icon='TRIA_UP', text="").type = 'UP'
            sub.operator("gpencil.layer_annotation_move", icon='TRIA_DOWN', text="").type = 'DOWN'

    tool_settings = context.tool_settings
    if gpd and gpl:
        layout.prop(gpl, "annotation_opacity", text="Opacity", slider=True)
        layout.prop(gpl, "thickness")
    else:
        layout.prop(tool_settings, "annotation_thickness", text="Thickness")

    if gpl:
        # Full-Row - Frame Locking (and Delete Frame)
        row = layout.row(align=True)
        row.active = not gpl.lock

        if gpl.active_frame:
            lock_status = iface_("Locked") if gpl.lock_frame else iface_("Unlocked")
            lock_label = iface_("Frame: {:d} ({:s})").format(gpl.active_frame.frame_number, lock_status)
        else:
            lock_label = iface_("Lock Frame")
        row.prop(gpl, "lock_frame", text=lock_label, icon='UNLOCKED')
        row.operator("gpencil.annotation_active_frame_delete", text="", icon='X')


def register():
    global OLD_DRAW
    OLD_DRAW = bpy.types.NODE_PT_annotation.draw
    bpy.types.NODE_PT_annotation.draw = draw


def unregister():
    global OLD_DRAW
    bpy.types.NODE_PT_annotation.draw = OLD_DRAW
    OLD_DRAW = None
