from enum import Enum
from typing import Final

from mathutils import Euler

from .utils import EulerTool


class ShootAngles(Enum):
    """Euler angles for the shooting.
    shoot will be on top(xy plane, z up), so the enum members are the angles to rotate the object to face the camera."""
    TOP_LEFT_FRONT: Euler = EulerTool.to_rad((-67.8044, -32.8686, -13.4876))
    TOP_LEFT_FRONT_45: Euler = EulerTool.to_rad((-35.2644, -30, -35.2644))

    TOP: Euler = EulerTool.to_rad((0, 0, 0))
    FRONT: Euler = EulerTool.to_rad((-90, 0, 0))
    LEFT: Euler = EulerTool.to_rad((0, -90, -90))
    RIGHT: Euler = EulerTool.to_rad((0, 90, 90))
    BOTTOM: Euler = EulerTool.to_rad((0, 180, 0))

    @classmethod
    def enum_shot_orient_items(cls) -> list[tuple[str, str, str]]:
        return [(euler.name, euler.name.replace('_', ' ').title(), '') for euler in cls]


class GPAddTypes(Enum):
    TEXT: str = "Text"
    OBJECT: str = "Object"
    BL_ICON: str = "Icon"

    @classmethod
    def enum_add_type_items(cls) -> list[tuple[str, str, str]]:
        return [(t.name, t.value, "") for t in cls]


class SocketColor(Enum):
    GREY: Final[str] = '#A1A1A1'  # float color
    ORANGE: Final[str] = '#ED9E5C'  # object color
    GREEN_GEO: Final[str] = '#00D6A3'  # geometry color
    GREEN_INT: Final[str] = '#598C5C'  # interface color
    BLUE: Final[str] = '#598AC3'  # string color
    PURPLE_VEC: Final[str] = '#6363C7'  # vector color
    PURPLE_IMG: Final[str] = '#633863'  # image color
    PINK_BOOL: Final[str] = '#CCA6D6'  # boolean color
    PINK_MAT: Final[str] = '#EB7582'  # material color


custom_colors = [
    '#ffffff',
    '#e5e5e5',
    '#a6a6a6',
    '#808080',
    '#383838',
    '#000000',
    '#ff5733',
    '#d4302f',
    '#d4302f',
    '#ffeb3c',
    '#ffc300',
    '#ff8d1a',
    '#a5d63f',
    '#44cf7c',
    '#00baad',
    '#2a82e4',
    '#7848ea',
]
