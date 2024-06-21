import bpy
from bpy.props import StringProperty, IntProperty, PointerProperty, FloatVectorProperty
from mathutils import Vector
from typing import ClassVar

from .model.utils import VecTool
from .model.model_draw import DrawModel
from .model.model_drag import DragGreasePencilModel
from .model.model_gp import CreateGreasePencilData
from .model.model_gp import BuildGreasePencilData
from .model.model_gp import GreasePencilLayerBBox
from .model.model_gp import GreasePencilLayers
from .ops_notes import has_edit_tree


def enum_add_type_items() -> list[tuple[str, str, str]]:
    """Return the items for the add_type enum property."""
    data: dict = {
        'TEXT': "Text",
        'OBJECT': "Object",
    }
    return [(key, value, "") for key, value in data.items()]


class ENN_OT_add_gp(bpy.types.Operator):
    bl_idname = "enn.add_gp"
    bl_label = "Add"
    bl_options = {'UNDO'}

    add_type: bpy.props.EnumProperty(
        name='Type',
        items=lambda self, context: enum_add_type_items(), options={'SKIP_SAVE', 'HIDDEN'}
    )

    text: StringProperty(name="Text", default="Hello World")
    size: IntProperty(name="Size", default=100)
    obj: StringProperty(name="Object", default="", options={'SKIP_SAVE', 'HIDDEN'})

    location: FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE', 'HIDDEN'})
    use_mouse_pos: bpy.props.BoolProperty(default=True, options={'SKIP_SAVE', 'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        self.mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        font_gp_data: bpy.types.GreasePencil = None

        if not gp_data:
            gp_data = CreateGreasePencilData.empty()

        if self.add_type == 'OBJECT':
            obj = bpy.data.objects.get(self.obj, None)
            if not obj:
                return {'CANCELLED'}
            if obj.type == 'MESH':
                font_gp_data = CreateGreasePencilData.from_mesh_obj(obj)
            elif obj.type == 'GPENCIL':
                font_gp_data = CreateGreasePencilData.from_gp_obj(obj)
            else:
                return {'CANCELLED'}
        elif self.add_type == 'TEXT':
            font_gp_data = CreateGreasePencilData.from_text(self.text, self.size)

        if not font_gp_data: return {'CANCELLED'}

        vec = VecTool.r2d_2_v2d(self.mouse_pos) if self.use_mouse_pos else self.location

        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.link(context) \
                .join(font_gp_data) \
                .set_active_layer(-1) \
                .move_active(vec, space='v2d') \
                .color_active('#E7E7E7') \
                .to_2d()

        return {'FINISHED'}


class ENN_OT_add_gp_modal(bpy.types.Operator):
    bl_idname = "enn.add_gp_modal"
    bl_label = "Add"
    bl_description = "Add Grease from %s"
    bl_options = {'UNDO'}

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
                               location=location)


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
        if not gp_data:
            return {'CANCELLED'}
        layer_index: int = gp_data.layers.active_index
        bbox = GreasePencilLayerBBox(gp_data)
        bbox.calc_active_layer_bbox()
        pivot = bbox.center
        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.rotate_active(self.rotate_angle, pivot)
        context.area.tag_redraw()
        return {'FINISHED'}


def draw_hover_callback_px(self: 'ENN_OT_gp_set_active_layer', context) -> None:
    if self.is_dragging:
        return
    drag_model: DragGreasePencilModel = self.drag_model
    gp_data_bbox: GreasePencilLayerBBox = drag_model.gp_data_bbox

    top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
    points = [top_left, top_right, bottom_left, bottom_right]
    coords = [top_left, top_right, bottom_right, bottom_left, top_left]  # close the loop

    draw_model: DrawModel = DrawModel(points, gp_data_bbox.edge_center_points_r2d, coords)
    draw_model.draw_bbox_edge()

    if drag_model.in_drag_area:
        draw_model.draw_bbox_points()
    if drag_model.on_edge_center:
        draw_model.draw_scale_edge_widget()
    if drag_model.on_corner:
        draw_model.draw_scale_corner_widget()
    elif drag_model.on_corner_extrude:
        draw_model.draw_rotate_widget(point=drag_model.on_corner_extrude)


class ENN_OT_gp_set_active_layer(bpy.types.Operator):
    bl_idname = "enn.gp_set_active_layer"
    bl_label = "Set Active Layer"
    bl_description = "Set the active layer of the Grease Pencil Object"
    # bl_options = {'UNDO'}

    draw_handle: ClassVar = None
    drag_model: ClassVar[DragGreasePencilModel] = None
    # call stop
    stop: bool = False
    is_dragging: ClassVar[bool] = False  # allow to call from other operator

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        self.stop = False
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        drag_model = DragGreasePencilModel(gp_data=gp_data)

        try:
            layer_index = GreasePencilLayers.in_layer_area(gp_data, (event.mouse_region_x, event.mouse_region_y))
        except ReferenceError:  # ctrl z
            layer_index = None
        except AttributeError:  # switch to other tool
            layer_index = None
        if layer_index is None:
            return {'FINISHED'}

        drag_model.gp_data_bbox.active_layer_index = layer_index
        drag_model.gp_data_bbox.calc_active_layer_bbox()
        self.__class__.drag_model = drag_model

        self.add_draw_handle(context)
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def remove_draw_handle(self):
        if self.draw_handle:
            bpy.types.SpaceNodeEditor.draw_handler_remove(self.draw_handle, 'WINDOW')
            self.__class__.draw_handle = None

    def add_draw_handle(self, context):
        if not self.__class__.draw_handle:
            self.__class__.draw_handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_hover_callback_px,
                                                                                    (self, context),
                                                                                    'WINDOW', 'POST_PIXEL')

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            try:
                self.drag_model.update_mouse_pos(context, event)
                self.drag_model.detect_near_widgets()
            except ReferenceError:  # ctrl z
                self.stop = True
            except AttributeError:  # switch to other tool
                self.stop = True
        # active tool is not drag tool
        if self.stop or event.type in {'ESC', 'RIGHTMOUSE'}:
            self.remove_draw_handle()
            context.area.tag_redraw()
            self.stop = False
            self.__class__.drag_model = None
            return {'FINISHED'}
        context.area.tag_redraw()
        return {'PASS_THROUGH'}


def draw_drag_callback_px(self: 'ENN_OT_gp_drag_modal', context) -> None:
    drag_model: DragGreasePencilModel = self.drag_model
    gp_data_bbox: GreasePencilLayerBBox = drag_model.gp_data_bbox

    top_left, top_right, bottom_left, bottom_right = gp_data_bbox.bbox_points_r2d
    points = [top_left, top_right, bottom_left, bottom_right]
    coords = [top_left, top_right, bottom_right, bottom_left, top_left]  # close the loop

    draw_model: DrawModel = DrawModel(points, gp_data_bbox.edge_center_points_r2d, coords)

    if draw_model.drag_area:
        draw_model.draw_bbox_area()
    if draw_model.drag:
        draw_model.draw_bbox_edge()

    if draw_model.debug:
        draw_model.draw_debug(self.drag_model.mouse_pos)


class ENN_OT_gp_drag_modal(bpy.types.Operator):
    bl_idname = "enn.gp_drag_modal"
    bl_label = "Transform"
    bl_description = "Move the active Grease Pencil Layer"
    bl_options = {'UNDO'}

    # model
    drag_model: DragGreasePencilModel = None
    draw_handle = None  # draw handle
    # is dragging
    drag_init: bool = False

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil

        self.drag_model = DragGreasePencilModel(gp_data=gp_data)
        self.draw_handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_drag_callback_px, (self, context), 'WINDOW',
                                                                      'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        self.drag_model.update_mouse_pos(context, event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if event.type == 'MOUSEMOVE':
            ENN_OT_gp_set_active_layer.is_dragging = True
            self.drag_model.update_mouse_pos(context, event)
            if not self.drag_init:
                self.drag_model.detect_near_widgets()
                self.drag_init = True
            self.drag_model.handle_drag(context, event)

        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE", "MIDDLEMOUSE"}:
            return {'PASS_THROUGH'}
        if event.type in {'ESC', 'RIGHTMOUSE'} or (event.type == 'LEFTMOUSE' and event.value == 'RELEASE'):
            self._finish(context)
            return {'FINISHED'}

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        ENN_OT_gp_set_active_layer.is_dragging = False
        ENN_OT_gp_set_active_layer.drag_model.update_gp_data(context)
        bpy.types.SpaceNodeEditor.draw_handler_remove(self.draw_handle, 'WINDOW')
        context.area.tag_redraw()


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
        op = box.operator(ENN_OT_add_gp_modal.bl_idname)
        op.add_type = context.window_manager.enn_gp_add_type

        # op = layout.operator(ENN_OT_move_gp.bl_idname)
        # op.move_vector = (50, 50)
        # op = layout.operator(ENN_OT_rotate_gp.bl_idname)
        # op.rotate_angle = 30

        # layout.separator()
        # box = layout.box()
        # box.label(text="Move Active Layer Modal")
        # box.operator(ENN_OT_gp_drag_modal.bl_idname)


class ENN_TL_grease_pencil_tool(bpy.types.WorkSpaceTool):
    bl_idname = "enn.grease_pencil_tool"
    bL_idname_fallback = "node.select_box"
    bl_space_type = 'NODE_EDITOR'
    bl_context_mode = None
    bl_label = "Draw"
    bl_icon = "ops.gpencil.stroke_new"
    # bl_widget = "PH_GZG_place_tool"
    bl_keymap = (
        (ENN_OT_gp_set_active_layer.bl_idname,
         {"type": "LEFTMOUSE", "value": "CLICK"},
         {"properties": []},  # [("deselect_all", True)]
         ),
        (ENN_OT_add_gp.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK', "shift": True},
         {"properties": [('use_mouse_pos', True), ('add_type', 'TEXT')]}
         ),
        (ENN_OT_gp_drag_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False},
         {"properties": []}),

    )

    def draw_settings(context, layout, tool):
        pass


def register():
    from bpy.utils import register_class, register_tool

    bpy.types.WindowManager.enn_gp_size = bpy.props.IntProperty(name="Size", default=100, subtype='PIXEL')
    bpy.types.WindowManager.enn_gp_add_type = bpy.props.EnumProperty(items=lambda self, context: enum_add_type_items())
    bpy.types.WindowManager.enn_gp_text = bpy.props.StringProperty(name="Text", default="Hello World")
    bpy.types.WindowManager.enn_gp_obj = bpy.props.PointerProperty(name='Object', type=bpy.types.Object,
                                                                   poll=lambda self, obj: obj.type in {'MESH',
                                                                                                       'GPENCIL'})
    bpy.types.WindowManager.enn_gp_move_dis = bpy.props.IntProperty(name='Distance', default=50)
    register_class(ENN_OT_add_gp)
    register_class(ENN_OT_add_gp_modal)
    register_class(ENN_OT_gp_set_active_layer)
    register_class(ENN_OT_move_gp)
    register_class(ENN_OT_rotate_gp)
    register_class(ENN_OT_gp_drag_modal)
    register_class(ENN_PT_gn_edit_panel)

    register_tool(ENN_TL_grease_pencil_tool, separator=True)


def unregister():
    from bpy.utils import unregister_class, unregister_tool

    unregister_class(ENN_OT_add_gp)
    unregister_class(ENN_OT_add_gp_modal)
    unregister_class(ENN_OT_gp_set_active_layer)
    unregister_class(ENN_OT_move_gp)
    unregister_class(ENN_OT_rotate_gp)
    unregister_class(ENN_OT_gp_drag_modal)
    unregister_class(ENN_PT_gn_edit_panel)

    unregister_tool(ENN_TL_grease_pencil_tool)
