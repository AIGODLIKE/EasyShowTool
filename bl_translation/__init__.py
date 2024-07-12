import bpy
import os
from pathlib import Path
import importlib

helpers = []
addon_package = __package__
addon_id = addon_package.split('.')[0]


class TranslationHelper():
    def __init__(self, name: str, data: dict, lang='zh_CN'):
        self.name = name
        self.translations_dict = dict()

        for src, src_trans in data.items():
            key = ("Operator", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans
            key = ("*", src)
            self.translations_dict.setdefault(lang, {})[key] = src_trans

    def register(self):
        try:
            bpy.app.translations.register(self.name, self.translations_dict)
        except(ValueError):
            pass

    def unregister(self):
        try:
            bpy.app.translations.unregister(self.name)
        except(ValueError):
            pass


def register():
    languages_dir = Path(__file__).parent

    for filename in os.listdir(languages_dir):
        if not filename.endswith('.py'): continue
        if filename == '__init__.py': continue

        module_name = filename[:-3]
        module = importlib.import_module('.' + module_name, package=addon_package)

        helper = TranslationHelper(addon_id + module_name, module.data)
        helpers.append(helper)

        if module_name == 'zh_CN':
            helper_HANS = TranslationHelper(addon_id + 'zh_HANS', module.data, lang='zh_HANS')
            helpers.append(helper_HANS)

    for h in helpers:
        h.register()


def unregister():
    for h in helpers:
        h.unregister()
    helpers.clear()
