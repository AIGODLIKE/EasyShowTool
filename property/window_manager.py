import bpy
from bpy.types import WindowManager as wm
from bpy.props import IntProperty, FloatVectorProperty,IntVectorProperty



def register():
    wm.enn_gp_move_vector = IntVectorProperty(name='Move Vector', size=2, default=(50, 50))
    wm.enn_gp_scale = FloatVectorProperty(name='Scale Vector', size=2, default=(1.1, 1.1))
    wm.enn_gp_rotate_angle = IntProperty(name='Rotate Angle', default=30)


def unregister():
    del wm.enn_gp_move_vector
    del wm.enn_gp_scale
    del wm.enn_gp_rotate_angle

