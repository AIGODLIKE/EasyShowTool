import gpu
import gpu.state
import gpu.shader
import bpy
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d

from mathutils import Vector
from typing import Sequence, Union
from .model.model_gp import GreasePencilLayerBBox
from .ops_gp import DragGreasePencilModel

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices


# import draw_circle
def draw_cursor():
    # 2D drawing code here
    pass


def draw_callback_px(self, context) -> None:
    # 2D drawing code here
    gpu.state.line_width_set(2)
    gpu.state.point_size_set(15)
    gpu.state.blend_set('ALPHA')
    drag_model: DragGreasePencilModel = self.drag_model
    gp_data_bbox: GreasePencilLayerBBox = drag_model.gp_data_bbox

    top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
    points = [top_left, top_right, bottom_left, bottom_right]
    coords = [top_left, top_right, bottom_right, bottom_left, top_left]

    if not self.is_dragging:
        # draw the bbox
        color = (1, 1, 1, 0.5)

        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        shader.uniform_float("color", color)
        batch.draw(shader)

        color = (1, 1, 1, 0.8)  # normal color
        color_hover = (1, 1, 0, 0.8)

        if drag_model.in_drag_area:
            shader.uniform_float("color", color)
            batch = batch_for_shader(shader, 'POINTS', {"pos": points})
            batch.draw(shader)
        if drag_model.on_edge_center:
            edge_points = gp_data_bbox.edge_center_points_r2d
            shader.uniform_float("color", color_hover)
            batch = batch_for_shader(shader, 'POINTS', {"pos": edge_points})
            batch.draw(shader)
        if drag_model.on_corner:
            shader.uniform_float("color", color_hover)
            batch = batch_for_shader(shader, 'POINTS', {"pos": points})
            batch.draw(shader)
        elif drag_model.on_corner_extrude:
            draw_circle_2d(drag_model.on_corner_extrude, (1, 0, 0, 0.8), radius=15, segments=32)

    if self.is_dragging:
        # draw the drag area
        color = (1, 1, 1, 0.2)
        shader.uniform_float("color", color)
        batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=indices)
        batch.draw(shader)

        # draw the bbox
        color = (0, 1, 0, 0.5)
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
        shader.uniform_float("color", color)
        batch.draw(shader)

    batch = batch_for_shader(shader, 'POINTS', {"pos": [drag_model.mouse_pos]})
    batch.draw(shader)
