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

from . import ops_notes,ops_gp, keymap, preferences

modules = [
    ops_notes,
    ops_gp,
    preferences,
    keymap
]


def register():
    for m in modules:
        m.register()


def unregister():
    for m in modules.reverse():
        m.unregister()
