import bpy

from contextlib import contextmanager


def is_4_3_0_higher() -> bool:
    return bpy.app.version >= (4, 3, 0)


def add_grease_pencil_empty(**kwargs) -> None:
    if is_4_3_0_higher():
        bpy.ops.object.grease_pencil_add(type='EMPTY', **kwargs)
    else:
        bpy.ops.object.gpencil_add(type='EMPTY', **kwargs)


def convert_to_grease_pencil(**kwargs) -> None:
    if is_4_3_0_higher():
        if "seam" in kwargs:
            del kwargs["seam"]
        bpy.ops.object.convert(target='GREASEPENCIL', **kwargs)
    else:
        bpy.ops.object.convert(target='GPENCIL', **kwargs)


@contextmanager
def transform_apply_wrapper(obj: bpy.types.Object):
    toggle_3d = False
    if hasattr(obj.data, 'dimensions'):
        if getattr(obj.data, 'dimensions') == '2D':
            obj.data.dimensions = '3D'
            toggle_3d = True
    yield
    if toggle_3d:
        obj.data.dimensions = '2D'
