import bpy


class NoteBuilder():
    def __init__(self, frame_node: bpy.types.Node):
        self.node = frame_node
        self.text_data: bpy.types.Text = frame_node.text

    @property
    def body(self):
        return self.text_data.as_string()

    @body.setter
    def body(self, value):
        self.text_data.from_string()

    def append(self, value):
        self.text_data.write(value)
