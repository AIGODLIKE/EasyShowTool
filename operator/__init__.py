from . import ops_notes, ops_gp_modal, ops_gp_basic, op_icon_viewer, op_doc_server


def register():
    ops_notes.register()
    ops_gp_basic.register()
    ops_gp_modal.register()
    op_icon_viewer.register()
    op_doc_server.register()


def unregister():
    ops_notes.unregister()
    ops_gp_modal.unregister()
    ops_gp_basic.unregister()
    op_icon_viewer.unregister()
    op_doc_server.unregister()
