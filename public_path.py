import bpy
from typing import Optional, Union, Any
from pathlib import Path


def get_pref(data_path: Optional[str] = None) -> Union[bpy.types.AddonPreferences, Any]:
    pref = bpy.context.preferences.addons.get(__package__).preferences
    if data_path is None:
        return pref

    # search attribute by path
    def search_attr(obj, path: str):
        if '.' in path:
            path = path.split('.')
            return search_attr(getattr(obj, path[0]), path[1])
        else:
            return getattr(obj, path)

    return search_attr(pref, data_path)


def get_asset_directory() -> Path:
    return Path(__file__).parent.joinpath('asset')


def get_tool_icon(icon_name: str) -> str:
    return get_asset_directory().joinpath('bl_ui_icon', 'icons_tool', icon_name).as_posix()


def get_svg_icon(name: Optional[str] = None) -> Union[str, None]:
    d = get_asset_directory().joinpath('bl_ui_icon', 'icons_svg')
    if not name:
        return d.as_posix()
    if (p := d.joinpath(name + '.svg')).exists():
        return p.as_posix()

    return None


def get_color_palettes_directory() -> Path:
    return get_asset_directory().joinpath('color_palette')


def get_color_palettes() -> dict[str, list[str]]:
    """Return the color palette directory and file names.
    """
    d = get_color_palettes_directory()
    # make dict with key as directory name and value as list of file names
    return {p.name: [f.stem for f in p.iterdir() if f.suffix == '.png'] for p in d.iterdir() if p.is_dir()}
