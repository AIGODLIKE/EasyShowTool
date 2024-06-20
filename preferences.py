import bpy
from bpy.props import IntProperty, PointerProperty, StringProperty, BoolProperty, FloatVectorProperty


class FontProperty(bpy.types.PropertyGroup):
    title: bpy.props.PointerProperty(type=bpy.types.VectorFont)


class Preference(bpy.types.AddonPreferences):
    bl_idname = __package__

    note_width: IntProperty(default=250, name='Width')
    note_height: IntProperty(default=200, name='Height')
    note_default: StringProperty(default='Note', name='Default Label')

    gp_color: FloatVectorProperty(name='Color', default=(1, 1, 1, 0.5), subtype='COLOR', size=4)
    gp_color_hover: FloatVectorProperty(name='Color Hover', default=(1, 1, 0, 0.8), subtype='COLOR', size=4)
    gp_color_area: FloatVectorProperty(name='Color Area', default=(1, 1, 1, 0.2), subtype='COLOR', size=4)

    gp_draw_line_width: IntProperty(default=1, name='Line Width')

    gp_draw_drag: BoolProperty(default=False, name='Drag')
    gp_draw_drag_area: BoolProperty(default=False, name='Drag Area')

    gp_detect_edge_px: IntProperty(default=20, name='Edge', subtype='PIXEL')
    gp_detect_corner_px: IntProperty(default=20, name='Corner', subtype='PIXEL')
    gp_detect_rotate_px: IntProperty(default=15, name='Rotate', subtype='PIXEL')

    debug_draw: BoolProperty(default=False, name='Debug')

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.use_property_split = True
        box.label(text="Note")
        box.prop(self, 'note_width')
        box.prop(self, 'note_height')
        box.prop(self, 'note_default')

        box = layout.box()
        box.use_property_split = True
        box.label(text="Grease Pencil")
        box.prop(self, 'gp_draw_line_width')
        box.prop(self, 'gp_draw_drag')
        box.prop(self, 'gp_draw_drag_area')
        box.label(text="Detect")
        box.prop(self, 'gp_detect_edge_px')
        box.prop(self, 'gp_detect_corner_px')
        box.prop(self, 'gp_detect_rotate_px')
        box.prop(self, 'debug_draw')


def register():
    from bpy.utils import register_class
    # bpy.utils.register_class(FontProperty)
    register_class(Preference)
    # bpy.types.Scene.VectorFont = bpy.props.PointerProperty(type=bpy.types.VectorFont)


def unregister():
    from bpy.utils import unregister_class
    unregister_class(Preference)
    # bpy.utils.unregister_class(FontProperty)
