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
from .public_path import get_pref

shader = gpu.shader.from_builtin('UNIFORM_COLOR')
indices = GreasePencilLayerBBox.indices


# import draw_circle
def draw_cursor():
    # 2D drawing code here
    pass


def draw_origin_bbox(drag_model: DragGreasePencilModel, d_color, points, coords):
    gpu.state.point_size_set(10)
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
    shader.uniform_float("color", d_color)
    batch.draw(shader)
    if drag_model.in_drag_area:
        shader.uniform_float("color", d_color)
        batch = batch_for_shader(shader, 'POINTS', {"pos": points})
        batch.draw(shader)


def draw_callback_px(self, context) -> None:
    # pref
    d_line_width: int = get_pref().gp_draw_line_width
    d_debug: bool = get_pref().debug_draw
    d_drag: bool = get_pref().gp_draw_drag
    d_drag_area: bool = get_pref().gp_draw_drag_area
    d_color = get_pref().gp_color
    d_color_hover = get_pref().gp_color_hover
    d_color_area = get_pref().gp_color_area
    d_edge_px = get_pref().gp_detect_edge_px
    d_corner_px = get_pref().gp_detect_corner_px
    d_rotate_px = get_pref().gp_detect_rotate_px

    # 2D drawing code here
    gpu.state.line_width_set(d_line_width)
    gpu.state.point_size_set(20)
    gpu.state.blend_set('ALPHA')
    drag_model: DragGreasePencilModel = self.drag_model
    gp_data_bbox: GreasePencilLayerBBox = drag_model.gp_data_bbox

    top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
    points = [top_left, top_right, bottom_left, bottom_right]
    coords = [top_left, top_right, bottom_right, bottom_left, top_left]

    if not self.is_dragging:
        # draw the bbox
        draw_origin_bbox(drag_model, d_color, points, coords)
        if drag_model.on_edge_center:
            gpu.state.point_size_set(d_edge_px)
            edge_points = gp_data_bbox.edge_center_points_r2d
            shader.uniform_float("color", d_color_hover)
            batch = batch_for_shader(shader, 'POINTS', {"pos": edge_points})
            batch.draw(shader)
        if drag_model.on_corner:
            gpu.state.point_size_set(d_corner_px)
            shader.uniform_float("color", d_color_hover)
            batch = batch_for_shader(shader, 'POINTS', {"pos": points})
            batch.draw(shader)
        elif drag_model.on_corner_extrude:
            gpu.state.point_size_set(d_rotate_px)
            draw_circle_2d(drag_model.on_corner_extrude, d_color_hover, radius=15, segments=32)

    if self.is_dragging:
        # draw the drag area
        # if d_prev:
        #     draw_origin_bbox(drag_model, d_color, points, coords)

        if d_drag_area:
            shader.uniform_float("color", d_color_area)
            batch = batch_for_shader(shader, 'TRIS', {"pos": points}, indices=indices)
            batch.draw(shader)

        if d_drag:  # draw the bbox
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": coords})
            shader.uniform_float("color", d_color)
            batch.draw(shader)

    if d_debug:
        color = (0, 1, 0, 0.5)
        shader.uniform_float("color", color)
        batch = batch_for_shader(shader, 'POINTS', {"pos": [drag_model.mouse_pos]})
        batch.draw(shader)
