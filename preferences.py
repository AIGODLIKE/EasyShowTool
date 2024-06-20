import bpy
from bpy.props import IntProperty, PointerProperty


class FontProperty(bpy.types.PropertyGroup):
    title: bpy.props.PointerProperty(type=bpy.types.VectorFont)


class Preference(bpy.types.AddonPreferences):
    bl_idname = __package__

    note_width: IntProperty(default=250)
    note_height: IntProperty(default=200)

    # font = PointerProperty(type=FontProperty)

    # font_regular: PointerProperty(type=bpy.types.VectorFont)
    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Note Size:")
        box.prop(self, 'note_width')
        box.prop(self, 'note_height')

        box = layout.box()
        box.label(text='Font')
        # box.prop(context.scene, 'VectorFont')
        # box.prop(self.font, 'title')

def register():
    # bpy.utils.register_class(FontProperty)
    bpy.utils.register_class(Preference)
    # bpy.types.Scene.VectorFont = bpy.props.PointerProperty(type=bpy.types.VectorFont)


def unregister():
    bpy.utils.unregister_class(Preference)
    # bpy.utils.unregister_class(FontProperty)
