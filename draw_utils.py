import gpu
import bpy
from gpu_extras.batch import batch_for_shader
from .gp_utils import GreasePencilBBox

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilBBox.indices


def clamp_points(points) -> list[tuple[int, int]]:
    """clamp the point to the region"""
    width, height = bpy.context.region.width, bpy.context.region.height
    return [(max(0, min(width, x)), max(0, min(height, y))) for x, y in points]


def in_area(pos, points: list[tuple[int, int]]) -> bool:
    """check if the pos is in the area defined by the points"""
    x, y = pos
    top_left, top_right, bottom_left, bottom_right = points
    if top_left[0] < x < top_right[0] and bottom_left[1] < y < top_left[1]:
        return True
    return False


def draw_callback_px(self, context) -> None:
    # 2D drawing code here
    gpu.state.line_width_set(2)
    gpu.state.point_size_set(20)
    gpu.state.blend_set('ALPHA')
    gp_data_bbox: GreasePencilBBox = self.gp_data_bbox

    points = clamp_points(gp_data_bbox.bbox_points_r2d)
    coords = [points[0], points[1], points[3], points[2], points[0]]
    if not self.is_dragging:
        # draw the bbox
        color = (1, 1, 1, 0.5)

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        shader.uniform_float("color", color)
        batch.draw(shader)

        # draw the corner points
        if in_area(self.mouse_pos, points):
            color = (1, 1, 1, 0.8)
            shader.uniform_float("color", color)
            batch = batch_for_shader(shader, 'POINTS', {"pos": points})
            batch.draw(shader)

    if self.is_dragging:
        delta = (self.mouse_pos[0] - self.drag_start_pos[0], self.mouse_pos[1] - self.drag_start_pos[1])
        points = clamp_points([(x + delta[0], y + delta[1]) for x, y in points])
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
