import bpy
from typing import Optional, Union, Any
from pathlib import Path


def get_pref(data_path: Optional[str] = None) -> Union[bpy.types.AddonPreferences, Any]:
    pref = bpy.context.preferences.addons.get(__package__).preferences
    if data_path is None:
        return pref

    # 递归查找属性
    def search_attr(obj, path: str):
        if '.' in path:
            path = path.split('.')
            return search_attr(getattr(obj, path[0]), path[1])
        else:
            return getattr(obj, path)

    return search_attr(pref, data_path)
