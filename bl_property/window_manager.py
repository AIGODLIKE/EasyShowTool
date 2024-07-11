import bpy
from bpy.types import WindowManager as wm
from bpy.props import IntProperty, FloatVectorProperty,IntVectorProperty,StringProperty



def register():
    wm.est_gp_move_vector = IntVectorProperty(name='Move Vector', size=2, default=(50, 50))
    wm.est_gp_scale = FloatVectorProperty(name='Scale Vector', size=2, default=(1.1, 1.1))
    wm.est_gp_rotate_angle = IntProperty(name='Rotate Angle', default=30)
    wm.est_gp_icon_filter = StringProperty(name="Icon", default="")

def unregister():
    del wm.est_gp_move_vector
    del wm.est_gp_scale
    del wm.est_gp_rotate_angle
    del wm.est_gp_icon_filter

