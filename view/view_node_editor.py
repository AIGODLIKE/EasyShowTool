import bpy
from mathutils import Color, Vector

from typing import Sequence, Union, ClassVar, Literal, Optional, Callable
from dataclasses import dataclass, field

from ..model.model_gp_bbox import GPencilLayerBBox
from ..model.model_draw import DrawData, DrawPreference
from ..view_model.view_model_drag import DragGreasePencilViewModal
from ..view_model.view_model_draw import DrawViewModel


class ViewDrawHandle:
    handle = None
    func: Union['ViewBasic', Callable]
    log: ClassVar[list[str]] = []

    def is_empty(self):
        return self.handle is None

    def add_to_node_editor(self, func: Union['ViewBasic', Callable], args: tuple):
        # print('add_to_node_editor', func.__class__.__name__)
        self.log.append('Add: ' + func.__class__.__name__)
        self.func = func
        if self.handle is None:
            self.handle = bpy.types.SpaceNodeEditor.draw_handler_add(func, args, 'WINDOW', 'POST_PIXEL')

    def remove_from_node_editor(self):
        # print('remove_from_node_editor', self.func.__class__.__name__)
        if self.handle:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.handle, 'WINDOW')
            self.handle = None


@dataclass
class ViewBasic:
    drag_vm: DragGreasePencilViewModal
    draw_data: DrawData = field(init=False)
    draw_preference: DrawPreference = field(init=False)
    draw_vm: DrawViewModel = field(init=False)
    # show state
    _visible: bool = True

    def __post_init__(self):
        if self.draw_preference.lazy_update:
            self.drag_vm.on_mouse_move.append(self.update)
            self.drag_vm.on_mouse_init.append(self.update)

    def __call__(self, *args, **kwargs):
        if self.drag_vm.build_model.is_empty(): return  # empty data
        if not self._visible: return
        if not self.draw_preference.lazy_update:
            self.update()
        self.draw()

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    def draw(self):
        """override this method to draw the view"""
        ...

    def update(self):
        """override this method to update the draw data"""
        ...


@dataclass
class ViewHover(ViewBasic):

    def __post_init__(self):
        gp_data_bbox: GPencilLayerBBox = self.drag_vm.bbox_model
        top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
        points = [top_left, top_right, bottom_left, bottom_right]

        self.draw_data = DrawData(points, gp_data_bbox.edge_center_points_r2d)
        self.draw_preference = DrawPreference()
        self.draw_vm = DrawViewModel(self.draw_data, self.draw_preference)

    def update(self):
        self.draw_vm.update_draw_data(points=self.drag_vm.bbox_model.bbox_points_r2d,
                                      edge_points=self.drag_vm.bbox_model.edge_center_points_r2d,
                                      layer_points=self.drag_vm.selected_layers_points_r2d,)

    def draw(self) -> None:
        self.draw_vm.draw_bbox_edge()

        if self.drag_vm.in_drag_area:
            self.draw_vm.draw_bbox_edge(highlight=True)
        if self.drag_vm.pos_edge_center:
            self.draw_vm.draw_scale_edge_widget()
        if self.drag_vm.pos_corner:
            self.draw_vm.draw_scale_corner_widget()
        if self.drag_vm.pos_corner_extrude:
            self.draw_vm.draw_rotate_widget(point=self.drag_vm.pos_corner_extrude)

        if self.drag_vm.selected_layers_points_r2d and self.draw_vm.debug:
            for points in self.drag_vm.selected_layers_points_r2d:
                self.draw_vm.draw_box(points)

        if self.draw_vm.debug:
            self.draw_vm.draw_debug_info(self.drag_vm.debug_info)


@dataclass
class ViewDrag(ViewBasic):
    def __post_init__(self):
        gp_data_bbox: GPencilLayerBBox = self.drag_vm.bbox_model

        self.draw_data: DrawData = DrawData(gp_data_bbox.bbox_points_r2d,
                                            gp_data_bbox.edge_center_points_r2d,
                                            mouse_state=self.drag_vm.mouse_state)
        self.draw_preference = DrawPreference()
        self.draw_vm = DrawViewModel(self.draw_data, self.draw_preference)

    def update(self):
        self.draw_vm.update_draw_data(points=self.drag_vm.bbox_model.bbox_points_r2d,
                                      edge_points=self.drag_vm.bbox_model.edge_center_points_r2d,
                                      mouse_state=self.drag_vm.mouse_state)

    def draw(self) -> None:
        if self.draw_vm.drag_area:
            self.draw_vm.draw_bbox_area()
        if self.draw_vm.drag:
            self.draw_vm.draw_bbox_edge()
            self.draw_vm.draw_bbox_points()
            self.draw_vm.draw_rotate_angle()
            self.draw_vm.draw_select_box()
        if self.draw_vm.debug:
            self.draw_vm.draw_debug_info(self.drag_vm.debug_info)
