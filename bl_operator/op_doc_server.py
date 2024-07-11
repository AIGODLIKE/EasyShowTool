import bpy
import socket
import subprocess
import threading
import sys
from pathlib import Path

_runtime = {
    # 'port': None,
    # 'thread': None,
    # 'pid': None,
}


def get_document_dir() -> Path:
    return Path(__file__).parent.parent.joinpath('docs')


class ServerThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process = None
        self.port = self.find_open_port()

    @staticmethod
    def find_open_port(start_port: int = 8001, end_port: int = 8999) -> int:
        for port in range(start_port, end_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                pass
        raise OSError('No open port found')

    def run(self):
        doc_dir = str(get_document_dir()).replace('\\', '/')
        python = str(sys.executable).replace('\\', '/')
        args = [python, '-m', 'http.server', str(self.port)]
        self.process = subprocess.Popen(args, cwd=doc_dir)

    def stop(self):
        if self.process:
            self.process.terminate()


class EST_OT_launch_doc(bpy.types.Operator):
    bl_idname = 'est.launch_doc'
    bl_label = 'Documentation'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if _runtime.get('thread'):
            _runtime['thread'].stop()
            _runtime['thread'] = None
        _runtime['thread'] = ServerThread()
        _runtime['thread'].start()
        bpy.ops.wm.url_open(url=f'http://localhost:{_runtime["thread"].port}')
        return {'FINISHED'}


def register():
    bpy.utils.register_class(EST_OT_launch_doc)


def unregister():
    bpy.utils.unregister_class(EST_OT_launch_doc)
    if _runtime.get('thread'):
        _runtime['thread'].stop()
        _runtime['thread'] = None
