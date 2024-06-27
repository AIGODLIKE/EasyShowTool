import bpy
import time
import threading

from bpy.props import PointerProperty
from bpy.app.handlers import persistent

from ..model.model_color import ColorPaletteModel


class MyPaletteGroup(bpy.types.PropertyGroup):
    palette: PointerProperty(type=bpy.types.Palette)


def register_later(lock, t):
    while not hasattr(bpy.context, 'scene'):
        time.sleep(3)
    # print("Start register palette")
    color_model = ColorPaletteModel()
    color_model.setup()
    bpy.context.scene.enn_palette_group.palette = color_model.palette


@persistent
def init_scene_props(noob):
    lock = threading.Lock()
    lock_holder = threading.Thread(target=register_later, args=(lock, 5), name='enn_color')
    lock_holder.daemon = True
    lock_holder.start()


def register():
    from bpy.utils import register_class

    register_class(MyPaletteGroup)
    bpy.types.Scene.enn_palette_group = bpy.props.PointerProperty(type=MyPaletteGroup)

    bpy.app.handlers.load_post.append(init_scene_props)


def unregister():
    from bpy.utils import unregister_class

    bpy.app.handlers.load_post.remove(init_scene_props)
    unregister_class(MyPaletteGroup)
    del bpy.types.Scene.enn_palette_group
