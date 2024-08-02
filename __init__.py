bl_info = {
    "name": "Easy Show Tool",
    "author": "Atticus, AIGODLIKE Community",
    "description": "Add Amazing notes to your node editor",
    "blender": (4, 2, 0),
    "version": (0, 2, 0),
    "location": "",
    "doc_url": "",
    "warning": "",
    "category": "Node"
}

from . import bl_operator, keymap, preferences, bl_workspace_tool, bl_property, bl_translation

modules = [
    bl_property,
    bl_operator,
    bl_workspace_tool,
    preferences,
    keymap,
    bl_translation
]


def register():
    for m in modules:
        m.register()


def unregister():
    for m in modules:
        m.unregister()
