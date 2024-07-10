import bpy
from bpy.props import IntProperty, PointerProperty, StringProperty, BoolProperty, FloatVectorProperty, EnumProperty, \
    FloatProperty
from bpy.app.translations import pgettext_iface as _p
from .operator.functions import enum_shot_orient_items


def draw_property_group(layout: bpy.types.UILayout, pointer: bpy.types.PointerProperty):
    layout.label(text=_p(pointer.text), icon=pointer.icon)
    for prop in pointer.__annotations__:
        layout.prop(pointer, prop)


class NoteProperty(bpy.types.PropertyGroup):
    label_size: IntProperty(default=20, name='Label Size')
    title: StringProperty(default='Note', name='Title')
    width: IntProperty(default=250, name='Width')
    height: IntProperty(default=200, name='Height')

    text = 'Add Note Operator'
    icon = 'TEXT'


class GreasePencilDrawProperty(bpy.types.PropertyGroup):
    line_width: IntProperty(default=1, name='Line Width')
    drag: BoolProperty(default=True, name='Draw Box When Dragging')
    drag_area: BoolProperty(default=False, name='Drag Box Area When Dragging')

    text = 'Draw'
    icon = 'EDITMODE_HLT'


class GreasePencilPerformanceProperty(bpy.types.PropertyGroup):
    # lazy_update: BoolProperty(default=False, name='Lazy Update')
    snap_degree: IntProperty(name='Rotate Snap Degree', default=15)
    detect_edge_px: IntProperty(default=20, name='Detect Edge Radius', subtype='PIXEL')
    detect_corner_px: IntProperty(default=20, name='Detect Corner Radius', subtype='PIXEL')
    detect_rotate_px: IntProperty(default=20, name='Detect Rotate Radius', subtype='PIXEL')

    text = 'Performance'
    icon = 'MODIFIER'


class Preference(bpy.types.AddonPreferences):
    bl_idname = __package__
    # add note operator
    note: PointerProperty(type=NoteProperty)
    # grease pencil
    gp_draw: PointerProperty(type=GreasePencilDrawProperty)
    gp_performance: PointerProperty(type=GreasePencilPerformanceProperty)
    # debug
    debug: BoolProperty(default=False, name='Debug')

    def draw(self, context):
        layout = self.layout
        col = layout.box().column()
        col.use_property_split = True
        draw_property_group(col, self.note)

        col = layout.box().column()
        col.use_property_split = True
        draw_property_group(col, self.gp_performance)

        col = layout.box().column()
        col.use_property_split = True
        draw_property_group(col, self.gp_draw)

        layout.prop(self, 'debug')


def register():
    from bpy.utils import register_class
    register_class(NoteProperty)
    register_class(GreasePencilDrawProperty)
    register_class(GreasePencilPerformanceProperty)
    register_class(Preference)


def unregister():
    from bpy.utils import unregister_class
    unregister_class(Preference)
    unregister_class(NoteProperty)
    unregister_class(GreasePencilDrawProperty)
    unregister_class(GreasePencilPerformanceProperty)
