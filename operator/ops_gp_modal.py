import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty, FloatVectorProperty, BoolProperty
from typing import ClassVar
from mathutils import Vector

from ..model.model_gp import CreateGreasePencilData, BuildGreasePencilData
from ..model.model_gp_bbox import GreasePencilLayerBBox, GreasePencilLayers
from ..model.utils import VecTool, ShootAngles, ColorTool
from ..model.model_color import ColorPaletteModel
from ..view_model.handlers import ScaleHandler, RotateHandler, MoveHandler
from ..view_model.view_model_drag import DragGreasePencilViewModal
from ..view_model.view_model_draw import DrawViewModel
from ..view.view_node_editor import ViewHover, ViewDrawHandle, ViewDrag

from .functions import has_edit_tree, tag_redraw, is_valid_workspace_tool, enum_add_type_items, enum_shot_orient_items


# noinspection PyPep8Naming


# noinspection PyPep8Naming
class ENN_OT_add_gp_modal(bpy.types.Operator):
    bl_idname = "enn.add_gp_modal"
    bl_label = "Add"
    bl_description = "Add Grease from %s"
    bl_options = {'UNDO', "GRAB_CURSOR", "BLOCKING"}

    add_type: bpy.props.EnumProperty(
        items=lambda self, context: enum_add_type_items(),
    )

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    @classmethod
    def description(cls, context, property):
        return cls.bl_description % property.add_type.title()

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        context.window.cursor_set('PICK_AREA')
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return {'CANCELLED'}
        if event.type == 'LEFTMOUSE':
            v2d_loc = VecTool.r2d_2_v2d((event.mouse_region_x, event.mouse_region_y))
            self._add(context, v2d_loc)
            return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def _add(self, context, location):
        if self.add_type == 'TEXT':
            bpy.ops.enn.add_gp('EXEC_DEFAULT',
                               add_type=self.add_type,
                               text=context.window_manager.enn_gp_text,
                               size=context.window_manager.enn_gp_size,
                               location=location)
        elif self.add_type == 'OBJECT':
            bpy.ops.enn.add_gp('EXEC_DEFAULT',
                               add_type=self.add_type,
                               size=context.window_manager.enn_gp_size,
                               obj=context.window_manager.enn_gp_obj.name,
                               obj_shot_angle=context.window_manager.enn_gp_obj_shot_angle,
                               location=location)


# noinspection PyPep8Naming
class ENN_OT_gp_set_active_layer(bpy.types.Operator):
    bl_idname = "enn.gp_set_active_layer"
    bl_label = "Set Active Layer"
    bl_description = "Set the active layer of the Grease Pencil Object"
    # bl_options = {'UNDO'}
    # set class variable because need to call from other operator
    # also this operator is designed to be modal and single instance
    draw_handle: ClassVar[ViewDrawHandle] = None
    view_hover: ClassVar[ViewHover] = None
    drag_vm: ClassVar[DragGreasePencilViewModal] = None
    # call stop
    stop: bool = False
    is_dragging: ClassVar[bool] = False  # allow to call from other operator

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        self.stop = False
        if self.draw_handle:
            self.draw_handle.remove_from_node_editor()

        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        drag_vm = DragGreasePencilViewModal(gp_data=gp_data)

        try:
            layer_index = GreasePencilLayers.in_layer_area(gp_data, (event.mouse_region_x, event.mouse_region_y))
        except ReferenceError:  # ctrl z
            layer_index = None
        except AttributeError:  # switch to other tool
            layer_index = None
        if layer_index is None:
            return {'FINISHED'}

        drag_vm.bbox_model.active_layer_index = layer_index
        drag_vm.bbox_model.calc_active_layer_bbox()
        self.__class__.drag_vm = drag_vm
        self.__class__.view_hover = ViewHover(self.drag_vm)
        self.__class__.draw_handle = ViewDrawHandle()

        self.draw_handle.add_to_node_editor(self.view_hover, (self, context))
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'MOUSEMOVE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'MIDDLEMOUSE'}:
            try:
                self.drag_vm.update_mouse_pos(context, event)
                self.drag_vm.update_near_widgets()
            except ReferenceError:  # ctrl z
                self.stop = True
            except AttributeError:  # switch to other tool
                self.stop = True
        # active tool is not drag tool
        if self.stop or event.type in {'ESC', 'RIGHTMOUSE'} or not context.area or not is_valid_workspace_tool(context):
            self.draw_handle.remove_from_node_editor()
            self.stop = False
            self.__class__.drag_vm = None
            self.__class__.view_hover = None
            tag_redraw()
            return {'FINISHED'}
        context.area.tag_redraw()
        return {'PASS_THROUGH'}


class ENN_OT_gp_set_active_layer_color(bpy.types.Operator):
    bl_idname = 'enn.gp_set_active_layer_color'
    bl_label = 'Set Active Layer Color'
    bl_description = 'Set the active layer color of the Grease Pencil Object'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        try:
            layer_index = GreasePencilLayers.in_layer_area(gp_data, (event.mouse_region_x, event.mouse_region_y))
        except ReferenceError:  # ctrl z
            layer_index = None
        except AttributeError:  # switch to other tool
            layer_index = None
        if layer_index is None:
            return {'FINISHED'}

        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.active_layer_index = layer_index
            color = context.scene.enn_palette_group.palette.colors.active.color
            gp_data_builder.color_active(color=color)
        return {'FINISHED'}


# noinspection PyPep8Naming
class ENN_OT_gp_drag_modal(bpy.types.Operator):
    bl_idname = "enn.gp_drag_modal"
    bl_label = "Transform"
    bl_description = "Move the active Grease Pencil Layer"
    bl_options = {'UNDO'}

    # drag view model is used to handle the drag event
    drag_vm: DragGreasePencilViewModal = None
    #  view is accept view model data and draw the view
    view_drag: ViewDrag = None
    # draw handle is used to set up or stop the draw
    draw_handle: ClassVar[ViewDrawHandle] = None
    # init drag because click drag will cover the mouse move event in the first time
    drag_init: bool = False

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil

        self.drag_vm = DragGreasePencilViewModal(gp_data=gp_data)
        self.view_drag = ViewDrag(self.drag_vm)

        self.drag_vm.drag_scale_handler = ScaleHandler(
            call_after=lambda h: setattr(self.view_drag.draw_data, 'delta_scale', h.delta_scale))
        self.drag_vm.drag_rotate_handler = RotateHandler(
            call_after=lambda h: setattr(self.view_drag.draw_data, 'delta_degree', h.delta_degree))
        self.drag_vm.drag_move_handler = MoveHandler(
            call_after=lambda h: setattr(self.view_drag.draw_data, 'delta_move', h.delta_move))

        self.__class__.draw_handle = ViewDrawHandle()
        self.__class__.draw_handle.add_to_node_editor(self.view_drag, (self, context))
        context.window_manager.modal_handler_add(self)
        self.drag_vm.update_mouse_pos(context, event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            if ENN_OT_gp_set_active_layer.view_hover:
                ENN_OT_gp_set_active_layer.view_hover.hide()
            self.drag_vm.update_mouse_pos(context, event)
            if not self.drag_init:
                self.drag_vm.mouse_init()
                self.drag_vm.update_near_widgets()
                self.drag_init = True
            self.drag_vm.handle_drag(context, event)

        if True in (
                event.type in {'ESC', 'RIGHTMOUSE'},
                event.type == 'LEFTMOUSE' and event.value == 'RELEASE',
                not is_valid_workspace_tool(context)
        ):
            self._finish(context)
            return {'FINISHED'}
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        self.draw_handle.remove_from_node_editor()
        ENN_OT_gp_set_active_layer.view_hover.show()
        if ENN_OT_gp_set_active_layer.drag_vm:
            ENN_OT_gp_set_active_layer.drag_vm._update_bbox(context)
        context.area.tag_redraw()


# noinspection PyPep8Naming
class ENN_PT_gn_edit_panel(bpy.types.Panel):
    bl_label = "Edit Grease Pencil Text"
    bl_idname = "ENN_PT_gn_edit_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'View'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.window_manager, "enn_gp_size")

        box = layout.box()
        box.label(text="Add")
        row = box.row()
        row.prop(context.window_manager, "enn_gp_add_type", expand=True)

        if context.window_manager.enn_gp_add_type == 'TEXT':
            box.prop(context.window_manager, "enn_gp_text")
        elif context.window_manager.enn_gp_add_type == 'OBJECT':
            box.prop(context.window_manager, "enn_gp_obj")
            box.prop(context.window_manager, "enn_gp_obj_shot_angle")
        op = box.operator(ENN_OT_add_gp_modal.bl_idname)
        op.add_type = context.window_manager.enn_gp_add_type

        if context.scene.enn_palette_group:
            layout.template_palette(context.scene.enn_palette_group, "palette", color=True)


class MyPaletteGroup(bpy.types.PropertyGroup):
    palette: bpy.props.PointerProperty(type=bpy.types.Palette)


def register():
    import threading
    import time
    from bpy.utils import register_class

    register_class(MyPaletteGroup)
    register_class(ENN_OT_add_gp_modal)
    register_class(ENN_OT_gp_set_active_layer)
    register_class(ENN_OT_gp_set_active_layer_color)
    register_class(ENN_OT_gp_drag_modal)
    register_class(ENN_PT_gn_edit_panel)

    bpy.types.WindowManager.enn_gp_size = bpy.props.IntProperty(name="Size", default=100, subtype='PIXEL')
    bpy.types.WindowManager.enn_gp_add_type = bpy.props.EnumProperty(items=lambda self, context: enum_add_type_items())
    bpy.types.WindowManager.enn_gp_text = bpy.props.StringProperty(name="Text", default="Hello World")
    bpy.types.WindowManager.enn_gp_obj = bpy.props.PointerProperty(name='Object', type=bpy.types.Object,
                                                                   poll=lambda self, obj: obj.type in {'MESH',
                                                                                                       'GPENCIL'})
    bpy.types.WindowManager.enn_gp_obj_shot_angle = bpy.props.EnumProperty(name="Shot Orientation",
                                                                           items=lambda _, __: enum_shot_orient_items())

    bpy.types.Scene.enn_palette_group = bpy.props.PointerProperty(type=MyPaletteGroup)
    bpy.types.WindowManager.enn_gp_move_dis = bpy.props.IntProperty(name='Distance', default=50)
    bpy.types.WindowManager.enn_gp_scale = bpy.props.FloatVectorProperty(name='Scale Vector', size=2,
                                                                         default=(1.1, 1.1))

    def register_later(lock, t):
        while not hasattr(bpy.context, 'scene'):
            time.sleep(3)
        # print("Start register palette")
        color_model = ColorPaletteModel()
        color_model.setup()
        bpy.context.scene.enn_palette_group.palette = color_model.palette

    lock = threading.Lock()
    lock_holder = threading.Thread(target=register_later, args=(lock, 5), name='enn_color')
    lock_holder.daemon = True
    lock_holder.start()


def unregister():
    from bpy.utils import unregister_class

    unregister_class(MyPaletteGroup)
    unregister_class(ENN_OT_add_gp_modal)
    unregister_class(ENN_OT_gp_set_active_layer_color)
    unregister_class(ENN_OT_gp_set_active_layer)

    unregister_class(ENN_OT_gp_drag_modal)
    unregister_class(ENN_PT_gn_edit_panel)
