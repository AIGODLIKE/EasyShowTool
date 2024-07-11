import bpy
import time
import threading

from bpy.props import PointerProperty, IntProperty, EnumProperty, StringProperty
from bpy.app.handlers import persistent

from ..model.model_color import ColorPaletteModel
from ..bl_operator.functions import enum_add_type_items, enum_shot_orient_items


class MyPaletteGroup(bpy.types.PropertyGroup):
    palette: PointerProperty(type=bpy.types.Palette)


def register_later(lock, t):
    while not hasattr(bpy.context, 'scene'):
        time.sleep(3)
    # print("Start register palette")
    color_model = ColorPaletteModel()
    color_model.setup()
    bpy.context.scene.est_palette_group.palette = color_model.palette

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
    from bpy.utils import register_class

    register_class(MyPaletteGroup)
    bpy.types.Scene.est_palette_group = PointerProperty(type=MyPaletteGroup)
    bpy.types.Scene.est_gp_transform_mode = EnumProperty(name="Transform Mode", items=[('LOCAL', 'Local', 'Local'),
                                                                                       ('GLOBAL', 'Global', 'Global')],
                                                         default='LOCAL')
    # add source
    bpy.types.Scene.est_gp_size = IntProperty(name="Size", default=100, subtype='PIXEL')
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
    from bpy.utils import unregister_class

    bpy.app.handlers.load_post.remove(init_scene_props)
    unregister_class(MyPaletteGroup)
    del bpy.types.Scene.est_palette_group
    del bpy.types.Scene.est_gp_size
    del bpy.types.Scene.est_gp_add_type
    del bpy.types.Scene.est_gp_text
    del bpy.types.Scene.est_gp_obj
    del bpy.types.Scene.est_gp_obj_shot_angle
    del bpy.types.Scene.est_gp_transform_mode
    del bpy.types.Space.est_gp_icon

