import bpy
from pathlib import Path


def get_pref() -> bpy.types.AddonPreferences:
    return bpy.context.preferences.addons.get(__package__).preferences
