import bpy
from bpy.props import StringProperty, EnumProperty
from typing import ClassVar
from mathutils import Vector

from ..model.model_gp import BuildGreasePencilData, CreateGreasePencilData
from ..model.model_gp_bbox import GPencilLayerBBox
from ..model.utils import VecTool
from ..view_model.handlers import ScaleHandler, RotateHandler, MoveHandler
from ..view_model.view_model_drag import DragGreasePencilViewModal
from ..view_model.view_model_select import SelectedGPLayersRuntime
from ..view.view_node_editor import ViewHover, ViewDrawHandle, ViewDrag
from ..view_model.view_model_mouse import MouseDragState

from .functions import has_edit_tree, tag_redraw, is_valid_workspace_tool, get_pos_layer_index, get_edit_tree_gp_data


class TransformModal(bpy.types.Operator):
    bl_options = {'UNDO', "GRAB_CURSOR", "BLOCKING"}
    build_model: BuildGreasePencilData = None
    bbox_model: GPencilLayerBBox = None

    move_handler: MoveHandler = None
    rotate_handler: RotateHandler = None
    scale_handler: ScaleHandler = None

    mouse_state: MouseDragState = None

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and get_edit_tree_gp_data(context) and is_valid_workspace_tool(context)

    def _init(self, context, event):
        gp_data = get_edit_tree_gp_data(context)
        self.build_model = BuildGreasePencilData(gp_data)
        self.bbox_model = GPencilLayerBBox(gp_data=self.build_model.gp_data, mode="LOCAL")
        self.bbox_model.calc_active_layer_bbox()
        self.mouse_state = MouseDragState()
        self.mouse_state.init(event)

    def _start_modal(self, context):
        context.window_manager.modal_handler_add(self)
        context.window.cursor_set('MOVE_X')
        EST_OT_gp_view.hide()

    def _finish(self, context) -> set:
        EST_OT_gp_view.show()
        SelectedGPLayersRuntime.update_from_gp_data(self.build_model.gp_data,
                                                    mode="LOCAL")
        context.area.tag_redraw()
        return {'FINISHED'}


class EST_OT_move_gp_modal(TransformModal):
    bl_idname = "est.move_gp_modal"
    bl_label = "Move"

    def invoke(self, context, event):
        self._init(context, event)

        self.move_handler = MoveHandler()
        self.move_handler.build_model = self.build_model
        self.move_handler.mouse_state = self.mouse_state

        self._start_modal(context)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._finish(context)
            return {'CANCELLED'}
        if event.type == 'MOUSEMOVE':
            self.mouse_state.update_mouse_position(event)
            self.move_handler.selected_layers = SelectedGPLayersRuntime.selected_layers()
            self.move_handler.accept_event(event)
        if event.type == 'LEFTMOUSE':
            self._finish(context)
            return {'FINISHED'}
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


class EST_OT_rotate_gp_modal(TransformModal):
    bl_idname = "est.rotate_gp_modal"
    bl_label = "Rotate"

    def invoke(self, context, event):
        self._init(context, event)

        self.rotate_handler = RotateHandler()

        self.rotate_handler.build_model = self.build_model
        self.rotate_handler.mouse_state = self.mouse_state
        self.rotate_handler.bbox_model = self.bbox_model

        self._start_modal(context)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._finish(context)
            return {'CANCELLED'}
        if event.type == 'MOUSEMOVE':
            self.mouse_state.update_mouse_position(event)
            self.rotate_handler.selected_layers = SelectedGPLayersRuntime.selected_layers()
            self.rotate_handler.accept_event(event)
        if event.type == 'LEFTMOUSE':
            self._finish(context)

            return {'FINISHED'}
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


class EST_OT_scale_gp_modal(TransformModal):
    bl_idname = "est.scale_gp_modal"
    bl_label = "Scale"

    def invoke(self, context, event):
        self._init(context, event)

        self.scale_handler = ScaleHandler()

        self.scale_handler.build_model = self.build_model
        self.scale_handler.mouse_state = self.mouse_state
        self.scale_handler.bbox_model = self.bbox_model
        self.scale_handler.force_center_scale = True

        self._start_modal(context)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._finish(context)
            return {'CANCELLED'}
        if event.type == 'MOUSEMOVE':
            self.mouse_state.update_mouse_position(event)
            self.scale_handler.selected_layers = SelectedGPLayersRuntime.selected_layers()
            self.scale_handler.accept_event(event)
        if event.type == 'LEFTMOUSE':
            self._finish(context)

            return {'FINISHED'}
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


# noinspection PyPep8Naming
class EST_OT_add_gp_modal(bpy.types.Operator):
    bl_idname = "est.add_gp_modal"
    bl_label = "Add"
    bl_description = "Add Grease from %s"
    bl_options = {'UNDO', "GRAB_CURSOR", "BLOCKING"}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and is_valid_workspace_tool(context)

    @classmethod
    def description(cls, context, property):
        return cls.bl_description % property.add_type.title()

    def invoke(self, context, event):
        self.add_type = context.scene.est_gp_add_type
        context.window_manager.modal_handler_add(self)
        context.window.cursor_set('PICK_AREA')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE':
            v2d_loc = VecTool.r2d_2_v2d(Vector((event.mouse_region_x, event.mouse_region_y)))
            res = self._add(self, context, v2d_loc)
            if res:
                SelectedGPLayersRuntime.clear()  # clear the selected layers
                SelectedGPLayersRuntime.set_active(get_edit_tree_gp_data(context).layers.active.info)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    @staticmethod
    def _add(self, context, location) -> bool:
        if self.add_type == 'TEXT':
            if context.scene.est_gp_text == '':
                self.report({'ERROR'}, "Empty")
                return False
            bpy.ops.est.add_gp('EXEC_DEFAULT',
                               add_type=self.add_type,
                               text=context.scene.est_gp_text,
                               size=context.scene.est_gp_size,
                               location=location)
            return True
        elif self.add_type == 'OBJECT':
            if not context.scene.est_gp_obj:
                self.report({'ERROR'}, "No object selected")
                return False
            bpy.ops.est.add_gp('EXEC_DEFAULT',
                               add_type=self.add_type,
                               size=context.scene.est_gp_size,
                               obj=context.scene.est_gp_obj.name,
                               obj_shot_angle=context.scene.est_gp_obj_shot_angle,
                               location=location)
            return True
        elif self.add_type == 'BL_ICON':
            bpy.ops.est.add_gp('EXEC_DEFAULT',
                               add_type=self.add_type,
                               size=context.scene.est_gp_size,
                               icon=context.scene.est_gp_icon,
                               location=location)
            return True
        return False


class EST_OT_drag_add_gp_modal(bpy.types.Operator):
    bl_idname = "est.drag_add_gp_modal"
    bl_label = "Add"
    bl_description = "Add %s"
    bl_options = {'UNDO', "GRAB_CURSOR", "BLOCKING"}

    mouse_state: MouseDragState = None
    drag_type: str = None
    drag_center: bool = False
    move_center: bool = False
    gp_data: bpy.types.GreasePencil
    build_model: BuildGreasePencilData = None
    bbox_model: GPencilLayerBBox = None
    gp_data_init: bool = False

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    @classmethod
    def description(cls, context, property):
        return cls.bl_description % property.add_type.title()

    def invoke(self, context, event):
        self.drag_add_type = context.scene.est_gp_drag_add_type
        self.add_type = context.scene.est_gp_add_type

        self.mouse_state = MouseDragState()
        self.mouse_state.init(event)
        self.gp_data = get_edit_tree_gp_data(context)
        ori_obj = context.object
        if self.gp_data is None:
            self.gp_data = CreateGreasePencilData.empty()
            context.space_data.edit_tree.grease_pencil = self.gp_data

        if self.drag_add_type == 'SQUARE':
            new_gp_data = CreateGreasePencilData.square(p1=VecTool.r2d_2_loc3d(self.mouse_state.start_pos),
                                                        p2=VecTool.r2d_2_loc3d(
                                                            self.mouse_state.end_pos + Vector((5, 5))))
        elif self.drag_add_type == 'CIRCLE':
            new_gp_data = CreateGreasePencilData.circle(center=VecTool.r2d_2_loc3d(self.mouse_state.start_pos),
                                                        radius=5)
        else:
            v2d_loc = VecTool.r2d_2_v2d(Vector((event.mouse_region_x, event.mouse_region_y)))
            EST_OT_add_gp_modal._add(self, context, v2d_loc)

        if self.drag_add_type in {'SQUARE', 'CIRCLE'}:
            with (BuildGreasePencilData(self.gp_data) as build_model):
                build_model.join(new_gp_data) \
                    .set_active_layer(-1) \
                    .move_active(VecTool.r2d_2_v2d(self.mouse_state.start_pos), space='v2d') \
                    .color_active(color=context.scene.est_palette_color) \
                    .opacity_active(context.scene.est_gp_opacity) \
                    .thickness_active(context.scene.est_gp_thickness)
        else:
            self.gp_data = get_edit_tree_gp_data(context)

            build_model = BuildGreasePencilData(self.gp_data)
        self.build_model = build_model
        self.bbox_model = GPencilLayerBBox(gp_data=self.build_model.gp_data, mode="LOCAL")
        context.view_layer.objects.active = ori_obj # restore the active object, if there is no gp data at first
        context.window_manager.modal_handler_add(self)
        context.window.cursor_set('PICK_AREA')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        self.drag_center = event.alt

        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return {'CANCELLED'}
        if event.type == 'MOUSEMOVE':
            self.mouse_state.update_mouse_position(event)
            pos1 = VecTool.r2d_2_loc3d(self.mouse_state.start_pos)
            pos2 = VecTool.r2d_2_loc3d(self.mouse_state.end_pos)

            if self.drag_center:
                size_3d = (pos2 - pos1) * 2
            else:
                size_3d = pos2 - pos1
            # avoid the size is too small
            for i in range(2):
                if abs(size_3d[i]) < 0.01:
                    size_3d[i] = 0.01
            if event.shift:
                size_3d = Vector((size_3d[0], size_3d[1], 1))

            self.build_model.fit_size(size_3d, fit_type='max' if event.shift else 'none',
                                      pivot_pos='center')
            if not self.drag_center and not event.shift:
                self.bbox_model.calc_active_layer_bbox()
                center = self.bbox_model.center_v2d
                drag_start_v2d = VecTool.r2d_2_v2d(self.mouse_state.start_pos)
                drag_end_v2d = VecTool.r2d_2_v2d(self.mouse_state.end_pos)
                drag_center = (drag_start_v2d + drag_end_v2d) / 2
                delta_v2d = drag_center.to_2d() - center.to_2d()
                self.build_model.move_active(delta_v2d, space='v2d')

            if self.gp_data_init is False:
                self.build_model.to_2d()
                self.gp_data_init = True

        if event.type == 'LEFTMOUSE':
            return {'FINISHED'}
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}


class EST_OT_gp_view(bpy.types.Operator):
    bl_idname = "est.gp_view"
    bl_label = "View"

    draw_handle: ClassVar[ViewDrawHandle] = None
    drag_vm: ClassVar[DragGreasePencilViewModal] = None
    view_hover: ClassVar[ViewHover] = None
    # call stop
    stop: bool = False

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and is_valid_workspace_tool(context) and get_edit_tree_gp_data(
            context) and (cls.draw_handle is None or cls.draw_handle.is_empty())

    @classmethod
    def hide(cls):
        if cls.view_hover:
            cls.view_hover.hide()

    @classmethod
    def show(cls):
        if cls.view_hover:
            cls.view_hover.show()
        if cls.drag_vm:
            cls.drag_vm._update_active_bbox(bpy.context)

    def invoke(self, context, event):
        self.stop = False
        if self.draw_handle:
            self.draw_handle.remove_from_node_editor()

        gp_data = get_edit_tree_gp_data(context)
        if not gp_data.layers.active:
            return {'CANCELLED'}
        drag_vm = DragGreasePencilViewModal(gp_data=gp_data)

        drag_vm.clear_selected_layers_points()
        drag_vm.bbox_model.calc_active_layer_bbox()
        self.__class__.drag_vm = drag_vm
        self.__class__.view_hover = ViewHover(self.drag_vm)
        self.__class__.draw_handle = ViewDrawHandle()

        self.draw_handle.add_to_node_editor(self.view_hover, (self, context))
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        self.drag_vm.set_bbox_mode("LOCAL")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self.stop or not context.area or not is_valid_workspace_tool(
                context) or not self.drag_vm or not self.drag_vm.has_active_layer():
            return self._finish()

        if event.type in {'MOUSEMOVE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MIDDLEMOUSE'}:
            self.update_drag_vm(context, event)
            if "LOCAL" != self.drag_vm.bbox_model.mode:
                self.drag_vm.set_bbox_mode("LOCAL")
            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    def update_drag_vm(self, context, event):
        try:
            self.drag_vm.update_mouse_pos(context, event)
            self.drag_vm.update_near_widgets()
        except ReferenceError:  # ctrl z
            self.stop = True
        except AttributeError:  # switch to other tool
            self.stop = True

    def _finish(self) -> set:
        self.draw_handle.remove_from_node_editor()
        self.stop = False
        self.__class__.drag_vm = None
        self.__class__.view_hover = None
        return {'FINISHED'}


# noinspection PyPep8Naming
class EST_OT_gp_set_active_layer(bpy.types.Operator):
    bl_idname = "est.gp_set_active_layer"
    bl_label = "Set Active Layer"
    bl_description = "Set the active layer of the Grease Pencil Object"

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and is_valid_workspace_tool(context) and get_edit_tree_gp_data(context)

    def invoke(self, context, event):
        gp_data = get_edit_tree_gp_data(context)

        if (layer_index := get_pos_layer_index(gp_data, (event.mouse_region_x, event.mouse_region_y),
                                               local=True)) is None:
            return {'FINISHED'}

        drag_vm = DragGreasePencilViewModal(gp_data=gp_data)
        layer = gp_data.layers[layer_index]

        if event.ctrl:  # subtraction select
            SelectedGPLayersRuntime.remove(layer.info)
        else:  # add select
            if not event.shift:  # single select active layer
                SelectedGPLayersRuntime.clear()

            drag_vm.build_model.active_layer_index = layer_index
            drag_vm.set_bbox_mode('LOCAL')
            drag_vm.bbox_model.calc_active_layer_bbox()
            points = list(drag_vm.bbox_model.bbox_points_v2d)
            points[2], points[3] = points[3], points[2]
            SelectedGPLayersRuntime.update(layer.info, points)
            # SelectedGPLayersRuntime.set_active(gp_data.layers.active.info)

        context.area.tag_redraw()
        return {'FINISHED'}


# noinspection PyPep8Naming
class EST_OT_gp_drag_modal(bpy.types.Operator):
    bl_idname = "est.gp_drag_modal"
    bl_label = "Transform"
    bl_description = "Move the active Grease Pencil Layer"
    bl_options = {'UNDO'}

    # drag view model is used to handle the drag event
    drag_vm: DragGreasePencilViewModal = None
    #  view is accept view model data and draw the view
    view_drag: ViewDrag = None
    # draw handle is used to set up or stop the draw
    draw_handle: ViewDrawHandle = None
    # init drag because click drag will cover the mouse move event in the first time
    drag_init: bool = False

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context) and is_valid_workspace_tool(context) and get_edit_tree_gp_data(context)

    def invoke(self, context, event):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil

        self.drag_vm = DragGreasePencilViewModal(gp_data=gp_data)
        self.view_drag = ViewDrag(self.drag_vm)

        self.drag_vm.drag_handles = {
            'SCALE': ScaleHandler(
                call_after=lambda h: setattr(self.view_drag.draw_data, 'delta_scale', h.delta_scale)
            ),
            'ROTATE': RotateHandler(
                call_after=lambda h: setattr(self.view_drag.draw_data, 'delta_degree', h.delta_degree)
            ),
            'MOVE': MoveHandler(
                call_after=lambda h: setattr(self.view_drag.draw_data, 'delta_move', h.delta_move)
            )
        }

        self.draw_handle = ViewDrawHandle()
        self.draw_handle.add_to_node_editor(self.view_drag, (self, context))
        context.window_manager.modal_handler_add(self)
        self.drag_vm.set_bbox_mode("LOCAL")
        self.drag_vm.update_mouse_pos(context, event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            EST_OT_gp_view.hide()
            self.drag_vm.update_mouse_pos(context, event)
            if not self.drag_init:
                self.drag_vm.mouse_init(event)
                self.drag_vm.update_near_widgets()
                self.drag_init = True
            self.drag_vm.handle_drag(context, event)
        # if event.type == 'B' and event.value == 'PRESS':
        #     self.drag_vm.toggle_bbox_mode()
        if True in (
                event.type in {'ESC', 'RIGHTMOUSE'},
                event.type == 'LEFTMOUSE' and event.value == 'RELEASE',
                not is_valid_workspace_tool(context)
        ):
            return self._finish(context)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def _finish(self, context) -> set:
        self.draw_handle.remove_from_node_editor()
        EST_OT_gp_view.show()
        SelectedGPLayersRuntime.update_from_gp_data(self.drag_vm.gp_data, mode="LOCAL")
        context.area.tag_redraw()
        return {'FINISHED'}


def register():
    from bpy.utils import register_class

    register_class(EST_OT_move_gp_modal)
    register_class(EST_OT_rotate_gp_modal)
    register_class(EST_OT_scale_gp_modal)
    register_class(EST_OT_add_gp_modal)
    register_class(EST_OT_gp_view)
    register_class(EST_OT_gp_set_active_layer)
    register_class(EST_OT_gp_drag_modal)
    register_class(EST_OT_drag_add_gp_modal)


def unregister():
    from bpy.utils import unregister_class
    EST_OT_gp_view.stop = True

    unregister_class(EST_OT_move_gp_modal)
    unregister_class(EST_OT_rotate_gp_modal)
    unregister_class(EST_OT_scale_gp_modal)
    unregister_class(EST_OT_add_gp_modal)
    unregister_class(EST_OT_gp_view)
    unregister_class(EST_OT_gp_set_active_layer)
    unregister_class(EST_OT_gp_drag_modal)
    unregister_class(EST_OT_drag_add_gp_modal)
