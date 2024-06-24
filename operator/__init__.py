from . import ops_notes,ops_gp_modal,ops_gp_basic


def register():
    ops_notes.register()
    ops_gp_basic.register()
    ops_gp_modal.register()


def unregister():
    ops_notes.unregister()
    ops_gp_modal.unregister()
    ops_gp_basic.unregister()
