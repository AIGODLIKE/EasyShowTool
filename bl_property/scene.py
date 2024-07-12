import bpy
import time
import threading

from bpy.props import PointerProperty, IntProperty, EnumProperty, StringProperty, FloatVectorProperty
from bpy.app.handlers import persistent

from ..model.model_color import ColorPaletteModel
from ..bl_operator.functions import enum_add_type_items, enum_shot_orient_items


def register_later(lock, t):
    while not hasattr(bpy.context, 'scene'):
        time.sleep(5)

    # font
    if bpy.context.scene.est_gp_text_font is None and 'Bfont Regular' not in bpy.data.fonts:
        bpy.data.curves.new('tmp', type='FONT')  # make sure the built-in font is loaded
        bpy.context.scene.est_gp_text_font = bpy.data.fonts['Bfont Regular']


@persistent
def init_scene_props(noob):
    lock = threading.Lock()
    lock_holder = threading.Thread(target=register_later, args=(lock, 5), name='est_color')
    lock_holder.daemon = True
    lock_holder.start()


def register():
    ColorPaletteModel.register_color_icon()

    bpy.types.Scene.est_palette_color = FloatVectorProperty(name="Color", size=3, subtype='COLOR_GAMMA', min=0.0, max=1.0,
                                                            default=(0.8, 0.8, 0.8))
    bpy.types.Scene.est_gp_transform_mode = EnumProperty(name="Transform Mode", items=[('LOCAL', 'Local', 'Local'),
                                                                                       ('GLOBAL', 'Global', 'Global')],
                                                         default='LOCAL')
    # add source
    bpy.types.Scene.est_gp_size = IntProperty(name="Size", default=500)
    bpy.types.Scene.est_gp_add_type = EnumProperty(items=lambda self, context: enum_add_type_items())
    bpy.types.Scene.est_gp_text = StringProperty(name="Text", default="Hello World")
    bpy.types.Scene.est_gp_text_font = PointerProperty(type=bpy.types.VectorFont)
    bpy.types.Scene.est_gp_obj = PointerProperty(name='Object', type=bpy.types.Object,
                                                 poll=lambda self, obj: obj.type in {'MESH', 'GPENCIL'})
    bpy.types.Scene.est_gp_obj_shot_angle = EnumProperty(name="Shot Orientation",
                                                         items=lambda _, __: enum_shot_orient_items())
    bpy.types.Scene.est_gp_icon = StringProperty(name="Icon", default="BLENDER")
    bpy.app.handlers.load_post.append(init_scene_props)


def unregister():
    ColorPaletteModel.unregister_color_icon()

    bpy.app.handlers.load_post.remove(init_scene_props)
    del bpy.types.Scene.est_gp_size
    del bpy.types.Scene.est_gp_add_type
    del bpy.types.Scene.est_gp_text
    del bpy.types.Scene.est_gp_obj
    del bpy.types.Scene.est_gp_obj_shot_angle
    del bpy.types.Scene.est_gp_transform_mode
    del bpy.types.Space.est_gp_icon
    del bpy.types.Space.est_palette_color
