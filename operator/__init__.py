from . import ops_notes,ops_gp


def register():
    ops_notes.register()
    ops_gp.register()


def unregister():
    ops_notes.unregister()
    ops_gp.unregister()
