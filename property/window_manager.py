import bpy
from bpy.types import WindowManager as wm
from bpy.props import EnumProperty, IntProperty, PointerProperty, StringProperty, FloatVectorProperty,IntVectorProperty

from ..operator.functions import enum_add_type_items, enum_shot_orient_items


def register():
    wm.enn_gp_size = IntProperty(name="Size", default=100, subtype='PIXEL')
    wm.enn_gp_add_type = EnumProperty(items=lambda self, context: enum_add_type_items())
    wm.enn_gp_text = StringProperty(name="Text", default="Hello World")
    wm.enn_gp_obj = PointerProperty(name='Object', type=bpy.types.Object,
                                    poll=lambda self, obj: obj.type in {'MESH', 'GPENCIL'})

    wm.enn_gp_obj_shot_angle = EnumProperty(name="Shot Orientation",
                                            items=lambda _, __: enum_shot_orient_items())

    wm.enn_gp_move_vector = IntVectorProperty(name='Move Vector', size=2, default=(50, 50))
    wm.enn_gp_scale = FloatVectorProperty(name='Scale Vector', size=2, default=(1.1, 1.1))
    wm.enn_gp_rotate_angle = IntProperty(name='Rotate Angle', default=30)


def unregister():
    del wm.enn_gp_size
    del wm.enn_gp_add_type
    del wm.enn_gp_text
    del wm.enn_gp_obj
    del wm.enn_gp_obj_shot_angle
    del wm.enn_gp_move_vector
    del wm.enn_gp_scale

