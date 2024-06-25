import bpy
from bpy.types import WindowManager as wm
from bpy.props import EnumProperty, IntProperty, PointerProperty, StringProperty, FloatVectorProperty

from ..operator.functions import enum_add_type_items, enum_shot_orient_items


def register():
    wm.enn_gp_size = IntProperty(name="Size", default=100, subtype='PIXEL')
    wm.enn_gp_add_type = EnumProperty(items=lambda self, context: enum_add_type_items())
    wm.enn_gp_text = StringProperty(name="Text", default="Hello World")
    wm.enn_gp_obj = PointerProperty(name='Object', type=bpy.types.Object,
                                    poll=lambda self, obj: obj.type in {'MESH', 'GPENCIL'})

    wm.enn_gp_obj_shot_angle = EnumProperty(name="Shot Orientation",
                                            items=lambda _, __: enum_shot_orient_items())

    wm.enn_gp_move_dis = IntProperty(name='Distance', default=50)
    wm.enn_gp_scale = FloatVectorProperty(name='Scale Vector', size=2, default=(1.1, 1.1))


def unregister():
    del wm.enn_gp_size
    del wm.enn_gp_add_type
    del wm.enn_gp_text
    del wm.enn_gp_obj
    del wm.enn_gp_obj_shot_angle
