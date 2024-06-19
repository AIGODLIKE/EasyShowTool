import bpy
from bpy.props import IntProperty


class Preference(bpy.types.AddonPreferences):
    bl_idname = __package__

    note_width: IntProperty(default=250)
    note_height: IntProperty(default=200)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Note Size:")
        box.prop(self, 'note_width')
        box.prop(self, 'note_height')

def register():
    bpy.utils.register_class(Preference)

def unregister():
    bpy.utils.unregister_class(Preference)