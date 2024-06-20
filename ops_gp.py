import bpy
from bpy.props import StringProperty, IntProperty, PointerProperty, FloatVectorProperty
from mathutils import Vector

from .model.utils import VecTool
from .model.model_drag import DragGreasePencilModel
from .model.model_gp import CreateGreasePencilData, MouseDetectModel
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
        items=lambda self, context: enum_add_type_items(),
    )

    text: StringProperty(name="Text", default="Hello World")
    size: IntProperty(name="Size", default=100)
    obj: StringProperty(name="Object", default="")

    location: FloatVectorProperty(size=2, default=(0, 0), options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
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

        with BuildGreasePencilData(gp_data) as gp_data_builder:
            gp_data_builder.link(context) \
                .join(font_gp_data) \
                .move(-1, self.location, space='v2d') \
                .color(-1, '#E7E7E7') \
                .to_2d()
            gp_data_builder.active_layer_index = -1

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


class ENN_OT_gp_set_active_layer(bpy.types.Operator):
    bl_idname = "enn.gp_set_active_layer"
    bl_label = "Set Active Layer"
    bl_description = "Set the active layer of the Grease Pencil Object"
    bl_options = {'UNDO'}

    mouse_pos: tuple[int, int] = (0, 0)

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        self.mouse_pos = event.mouse_region_x, event.mouse_region_y
        return self.execute(context)

    def execute(self, context):
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil
        if not gp_data: return {'CANCELLED'}
        bbox = GreasePencilLayerBBox(gp_data)
        MouseDetectModel(bbox)

        layer_index = GreasePencilLayers.in_layer_area(gp_data, self.mouse_pos)
        if layer_index is None:
            return {'CANCELLED'}
        else:
            bbox.active_layer_index = layer_index
            bbox.calc_active_layer_bbox()
        context.area.tag_redraw()

        return {'FINISHED'}


class ENN_OT_gp_modal(bpy.types.Operator):
    bl_idname = "enn.gp_modal"
    bl_label = "Transform"
    bl_description = "Move the selected Grease Pencil Object"
    bl_options = {'UNDO'}

    # model
    drag_model: DragGreasePencilModel = None
    # state
    draw_handle = None  # draw handle
    press_timer = None  # timer for detect long press

    is_pressing: bool = False
    press_value: str = None  # key press

    is_dragging: bool = False  # dragging

    # debug

    @classmethod
    def poll(cls, context):
        return has_edit_tree(context)

    def invoke(self, context, event):
        from .draw_utils import draw_callback_px
        nt: bpy.types.NodeTree = context.space_data.edit_tree
        gp_data: bpy.types.GreasePencil = nt.grease_pencil

        self.drag_model = DragGreasePencilModel(gp_data_bbox=GreasePencilLayerBBox(gp_data),
                                                gp_data_builder=BuildGreasePencilData(gp_data),
                                                mouse_pos=(0, 0),
                                                mouse_pos_prev=(0, 0),
                                                delta_vec=Vector((0, 0)))
        MouseDetectModel(self.drag_model.gp_data_bbox)

        self.press_timer = context.window_manager.event_timer_add(0.05, window=context.window)
        self.draw_handle = bpy.types.SpaceNodeEditor.draw_handler_add(draw_callback_px, (self, context), 'WINDOW',
                                                                      'POST_PIXEL')
        self.drag_model.update_gp_data(context)

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # handle drag
        if self._handle_pass_through(event):
            return {'PASS_THROUGH'}
        if self._handle_finish(context, event):
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            self.drag_model.handle_mouse_move_event(context, event)
            self.drag_model.handle_drag(event)

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        bpy.types.SpaceNodeEditor.draw_handler_remove(self.draw_handle, 'WINDOW')
        context.window.cursor_modal_restore()
        context.area.tag_redraw()
        if self.press_timer:
            context.window_manager.event_timer_remove(self.press_timer)
            self.press_timer = None

    def _handle_finish(self, context, event) -> bool:
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self._finish(context)
            return True

    def _handle_pass_through(self, event) -> bool:
        if event.type in {"WHEELUPMOUSE", "WHEELDOWNMOUSE", "MIDDLEMOUSE"}:
            return True
        return False


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

        layout.separator()
        box = layout.box()
        box.label(text="Move Active Layer Modal")
        box.operator(ENN_OT_gp_modal.bl_idname)


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

        (ENN_OT_gp_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": False},
         {"properties": []}),

        (ENN_OT_gp_modal.bl_idname,
         {"type": 'LEFTMOUSE', "value": 'CLICK_DRAG', "shift": True},
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
    register_class(ENN_OT_gp_modal)
    register_class(ENN_PT_gn_edit_panel)

    register_tool(ENN_TL_grease_pencil_tool, separator=True)


def unregister():
    from bpy.utils import unregister_class, unregister_tool

    unregister_class(ENN_OT_add_gp)
    unregister_class(ENN_OT_add_gp_modal)
    unregister_class(ENN_OT_gp_set_active_layer)
    unregister_class(ENN_OT_move_gp)
    unregister_class(ENN_OT_rotate_gp)
    unregister_class(ENN_OT_gp_modal)
    unregister_class(ENN_PT_gn_edit_panel)

    unregister_tool(ENN_TL_grease_pencil_tool)
