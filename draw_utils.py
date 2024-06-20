import gpu
import bpy
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from typing import Sequence, Union
from .gp_utils import GreasePencilLayerBBox

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices


def in_area(pos: Union[Sequence, Vector], points: list[Vector], feather: int = 20) -> bool:
    """check if the pos is in the area defined by the points
    :param pos: the position to check
    :param points: the points defining the area
    :param feather: the feather to expand the area, unit: pixel
    :return: True if the pos is in the area, False otherwise
    """
    x, y = pos
    top_left, top_right, bottom_left, bottom_right = points

    top_left = (top_left[0] - feather, top_left[1] + feather)
    top_right = (top_right[0] + feather, top_right[1] + feather)
    bottom_left = (bottom_left[0] - feather, bottom_left[1] - feather)

    if top_left[0] < x < top_right[0] and bottom_left[1] < y < top_left[1]:
        return True
    return False


def near_points(pos: Union[Sequence, Vector], points: list[Vector], radius: int = 20) -> Union[Vector, None]:
    """check if the pos is near the edge center of the area defined by the points
    :param pos: the position to check
    :param points: the points defining the area
    :param feather: the feather to expand the area, unit: pixel
    :return: True if the pos is near the edge center, False otherwise
    """
    vec_pos = Vector((pos[0], pos[1]))
    for point in points:
        vec_point = Vector(point)
        if (vec_pos - vec_point).length < radius:
            return vec_point
    return None


def draw_callback_px(self, context) -> None:
    # 2D drawing code here
    gpu.state.line_width_set(2)
    gpu.state.point_size_set(20)
    gpu.state.blend_set('ALPHA')
    gp_data_bbox: GreasePencilLayerBBox = self.gp_data_bbox

    top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
    points = [top_left, top_right, bottom_left, bottom_right]
    coords = [top_left, top_right, bottom_right, bottom_left, top_left]

    if not self.is_dragging:
        # draw the bbox
        color = (1, 1, 1, 0.5)

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        shader.uniform_float("color", color)
        batch.draw(shader)

        if in_area(self.mouse_pos, points):
            color = (1, 1, 1, 0.8)
            shader.uniform_float("color", color)
            batch = batch_for_shader(shader, 'POINTS', {"pos": points})
            batch.draw(shader)

    if self.is_dragging:
        delta = (self.mouse_pos[0] - self.drag_start_pos[0], self.mouse_pos[1] - self.drag_start_pos[1])
        points = [(x + delta[0], y + delta[1]) for x, y in points]
        coords = [points[0], points[1], points[3], points[2], points[0]]

        # draw the drag area
        # color = (1, 1, 1, 0.2)
        # shader.uniform_float("color", color)
        # batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=indices)
        # batch.draw(shader)

        # draw the bbox
        color = (1, 1, 1, 0.5)
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        shader.uniform_float("color", color)
        batch.draw(shader)
