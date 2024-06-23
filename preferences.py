import bpy
from bpy.props import IntProperty, PointerProperty, StringProperty, BoolProperty, FloatVectorProperty


class FontProperty(bpy.types.PropertyGroup):
    title: bpy.props.PointerProperty(type=bpy.types.VectorFont)


class Preference(bpy.types.AddonPreferences):
    bl_idname = __package__
    # add note operator
    note_title: StringProperty(default='Note', name='Title')
    note_width: IntProperty(default=250, name='Width')
    note_height: IntProperty(default=200, name='Height')
    note_default: StringProperty(default='Note', name='Default Label')

    gp_snap_degree: IntProperty(name='Rotate Snap Degree', default=15)

    # draw preference
    gp_draw_line_width: IntProperty(default=1, name='Line Width')
    gp_draw_drag: BoolProperty(default=True, name='Draw Box When Dragging')
    gp_draw_drag_area: BoolProperty(default=False, name='Drag Box Area When Dragging')
    # performance
    gp_draw_lazy_update: BoolProperty(default=False, name='Lazy Update')
    gp_detect_edge_px: IntProperty(default=20, name='Detect Edge Radius', subtype='PIXEL')
    gp_detect_corner_px: IntProperty(default=20, name='Detect Corner Radius', subtype='PIXEL')
    gp_detect_rotate_px: IntProperty(default=20, name='Detect Rotate Radius', subtype='PIXEL')
    # debug
    debug_draw: BoolProperty(default=False, name='Debug')

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.use_property_split = True
        box.label(text="Add Note Operator")
        box.prop(self, 'note_title')
        box.prop(self, 'note_width')
        box.prop(self, 'note_height')
        box.prop(self, 'note_default')

        box = layout.box()
        box.use_property_split = True
        box.label(text="Grease Pencil Edit Tool")

        box.label(text='Behavior')
        box.prop(self, 'gp_snap_degree')

        box.label(text="Performance")
        box.prop(self, 'gp_detect_edge_px')
        box.prop(self, 'gp_detect_corner_px')
        box.prop(self, 'gp_detect_rotate_px')
        box.prop(self, 'debug_draw')

        box.label(text="Draw")
        box.prop(self, 'gp_draw_drag')
        box.prop(self, 'gp_draw_drag_area')
        box.prop(self, 'gp_draw_line_width')


def register():
    from bpy.utils import register_class
    # bpy.utils.register_class(FontProperty)
    register_class(Preference)
    # bpy.types.Scene.VectorFont = bpy.props.PointerProperty(type=bpy.types.VectorFont)


def unregister():
    from bpy.utils import unregister_class
    unregister_class(Preference)
    # bpy.utils.unregister_class(FontProperty)
