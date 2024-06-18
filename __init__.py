bl_info = {
    "name": "Easy Node Notes",
    "author": "Atticus",
    "description": "Adds notes to your node editor",
    "blender": (4, 1, 0),
    "version": (0, 0, 1),
    "location": "",
    "doc_url": "",
    "warning": "",
    "category": "Node"
}

from . import ops_notes,keymap


def register():
    ops_notes.register()
    keymap.register()


def unregister():
    keymap.unregister()
    ops_notes.unregister()
