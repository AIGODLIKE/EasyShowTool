from . import scene,window_manager

def register():
    scene.register()
    window_manager.register()

def unregister():
    scene.unregister()
    window_manager.unregister()