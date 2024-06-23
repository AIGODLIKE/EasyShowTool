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
from .functions import has_edit_tree, tag_redraw, is_valid_workspace_tool
from ..view.view_node_editor import ViewHover, ViewDrawHandle, ViewDrag


def enum_add_type_items() -> list[tuple[str, str, str]]:
    """Return the items for the add_type enum property."""
    data: dict = {
        'TEXT': "Text",
        'OBJECT': "Object",
    }
    return [(key, value, "") for key, value in data.items()]


def enum_shot_orient_items() -> list[tuple[str, str, str]]:
    """Return the items for the shot_orient enum property."""
    return [(euler.name, euler.name.replace('_', ' ').title(), '') for euler in ShootAngles]


# noinspection PyPep8Naming
class ENN_OT_add_gp(bpy.types.Operator):
    bl_idname = "enn.add_gp"
    bl_label = "Add Amazing Note"
    bl_options = {'UNDO'}

    add_type: bpy.props.EnumProperty(name='Type',
                                     items=lambda _, __: enum_add_type_items(),
                                     options={'SKIP_SAVE', 'HIDDEN'})

    text: StringProperty(name="Text", default="Hello World")
    size: IntProperty(name="Size", default=100)
    obj: StringProperty(name="Object", default="", options={'SKIP_SAVE', 'HIDDEN'})
    obj_shot_angle: EnumProperty(name="Shot Orientation",
                                 items=lambda _, __: enum_shot_orient_items(),
                                 options={'SKIP_SAVE', 'HIDDEN'})

    location: FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE', 'HIDDEN'})
    use_mouse_pos: BoolProperty(default=False, options={'SKIP_SAVE', 'HIDDEN'})
    # mouse position
    mouse_pos: tuple[int, int] = (0, 0)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        return context.window_manager.invoke_props_dialog(self)

    def handle_invalid_input(self) -> bool:
        if self.add_type == 'OBJECT' and not bpy.data.objects.get(self.obj, None):
            return True
        elif self.add_type == 'TEXT' and self.text != '':
            return True
        return False

    def execute(self, context: bpy.types.Context):
        if not self.handle_invalid_input(): return {'CANCELLED'}

        font_gp_data: bpy.types.GreasePencil = None
        obj: bpy.types.Object = bpy.data.objects.get(self.obj, None)
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        vec: Vector = VecTool.r2d_2_v2d(self.mouse_pos) if self.use_mouse_pos else self.location
        gp_data: bpy.types.GreasePencil = CreateGreasePencilData.empty() if not nt.grease_pencil else nt.grease_pencil

        if self.add_type == 'TEXT':
            font_gp_data = CreateGreasePencilData.from_text(self.text, self.size)
        elif self.add_type == 'OBJECT':
            euler = getattr(ShootAngles, self.obj_shot_angle)
            if obj.type == 'MESH':
                font_gp_data = CreateGreasePencilData.from_mesh_obj(obj, euler=euler)
            elif obj.type == 'GPENCIL':
                font_gp_data = CreateGreasePencilData.from_gp_obj(obj, euler=euler)
            else:
                return {'CANCELLED'}

        if not font_gp_data: return {'CANCELLED'}

        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.link(context).join(font_gp_data) \
                .set_active_layer(-1).move_active(vec, space='v2d').color_active('#E7E7E7').to_2d()

        return {'FINISHED'}


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


class ENN_OT_remove_gp(bpy.types.Operator):
    bl_idname = "enn.remove_gp"
    bl_label = "Remove"
    bl_description = "Remove the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.remove_active_layer()
        return {'FINISHED'}


# noinspection PyPep8Naming
class ENN_OT_move_gp(bpy.types.Operator):
    bl_idname = "enn.move_gp"
    bl_label = "Move"
    bl_description = "Move the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    move_vector: bpy.props.IntVectorProperty(name='Move Vector', size=2, default=(50, 50))

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data:
            return {'CANCELLED'}
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.move_active(self.move_vector)
        context.area.tag_redraw()
        return {'FINISHED'}


# noinspection PyPep8Naming
class ENN_OT_rotate_gp(bpy.types.Operator):
    bl_idname = "enn.rotate_gp"
    bl_label = "Rotate"
    bl_description = "Rotate the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    rotate_angle: bpy.props.IntProperty(name='Rotate Angle', default=30)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}

        bbox = GreasePencilLayerBBox(gp_data)
        bbox.calc_active_layer_bbox()
        pivot = bbox.center
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.rotate_active(self.rotate_angle, pivot,space='v2d')
        context.area.tag_redraw()
        return {'FINISHED'}


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

    # model
    drag_vm: DragGreasePencilViewModal = None
    draw_handle: ClassVar[ViewDrawHandle] = None
    view_drag: ViewDrag = None

    drag_init: bool = False

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil

        self.drag_vm = DragGreasePencilViewModal(gp_data=gp_data)
        self.view_drag = ViewDrag(self.drag_vm)

        self.drag_vm.drag_scale_handler = ScaleHandler()
        self.drag_vm.drag_rotate_handler = RotateHandler()
        self.drag_vm.drag_move_handler = MoveHandler()

        self.__class__.draw_handle = ViewDrawHandle()
        self.__class__.draw_handle.add_to_node_editor(self.view_drag, (self, context))
        context.window_manager.modal_handler_add(self)
        self.drag_vm.update_mouse_pos(context, event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            ENN_OT_gp_set_active_layer.view_hover.hide()
            self.drag_vm.update_mouse_pos(context, event)
            if not self.drag_init:
                self.drag_vm.mouse_init()
                self.drag_vm.update_near_widgets()
                self.drag_init = True
            self.drag_vm.handle_drag(context, event)

        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE", "MIDDLEMOUSE"}:
            self.view_drag.update()
            return {'PASS_THROUGH'}
        if event.type in {'ESC', 'RIGHTMOUSE'} or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            self._finish(context)
            return {'FINISHED'}
        if not is_valid_workspace_tool(context):
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
    register_class(ENN_OT_add_gp)
    register_class(ENN_OT_add_gp_modal)
    register_class(ENN_OT_remove_gp)
    register_class(ENN_OT_gp_set_active_layer)
    register_class(ENN_OT_gp_set_active_layer_color)
    register_class(ENN_OT_move_gp)
    register_class(ENN_OT_rotate_gp)
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
    unregister_class(ENN_OT_add_gp)
    unregister_class(ENN_OT_add_gp_modal)
    unregister_class(ENN_OT_remove_gp)
    unregister_class(ENN_OT_gp_set_active_layer_color)
    unregister_class(ENN_OT_gp_set_active_layer)
    unregister_class(ENN_OT_move_gp)
    unregister_class(ENN_OT_rotate_gp)
    unregister_class(ENN_OT_gp_drag_modal)
    unregister_class(ENN_PT_gn_edit_panel)
