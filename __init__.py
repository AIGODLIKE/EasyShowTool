bl_info = {
    "name": "Easy Show Tool",
    "author": "Atticus, AIGODLIKE Community",
    "description": "Add Amazing notes to your node editor",
    "blender": (4, 1, 0),
    "version": (0, 1, 0),
    "location": "",
    "doc_url": "",
    "warning": "",
    "category": "Node"
}

from . import operator, keymap, preferences, workspace_tool, property, translation

modules = [
    property,
    operator,
    workspace_tool,
    preferences,
    keymap,
    translation
]


def register():
    for m in modules:
        m.register()


def unregister():
    for m in modules:
        m.unregister()
