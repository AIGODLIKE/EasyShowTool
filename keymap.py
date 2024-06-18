import bpy
from .ops_notes import ENN_OT_edit_note

addon_keymaps = []


def register():
    wm = bpy.context.window_manager
    if not wm.keyconfigs.addon: return

    km = wm.keyconfigs.addon.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    kmi = km.keymap_items.new(ENN_OT_edit_note.bl_idname, 'LEFTMOUSE', 'DOUBLE_CLICK', ctrl=False, shift=False)
    addon_keymaps.append((km, kmi))

def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc: return

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

    addon_keymaps.clear()