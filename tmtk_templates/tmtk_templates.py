"""
Copyright © 2023 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import bpy
import glob
from bpy.types import Operator, Menu
from mathutils import Vector, Matrix
from bpy.props import BoolProperty, StringProperty, EnumProperty
from bpy_extras import object_utils
from bpy.utils import resource_path
import os
import re

TEMPLATE_DIR = "templates"

currentPath = None

def get_items(self, context):
    global currentPath
    variants = getVariants(currentPath)
    return variants

def getVariants(path):
    if path == None:
        return []
    split = os.path.split(path)
    candidates = list(glob.iglob('**.fbx', root_dir = os.path.join(fullpath, split[0]), recursive=True))
    filename_base = re.match("(.+).fbx", split[1])[1]
    variants = sorted(list(filter(lambda x: re.match(filename_base + "(_\dm)?.fbx", x) != None, candidates)))
    variants = [(j, j, '', '', i) for i, j in enumerate(variants)]

    return variants

class AddTMTKTemplate(Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.tmtk_template_add"
    bl_label = "Add Template"
    bl_description = "Add a template"
    bl_options = {'REGISTER', 'UNDO'}

    change : BoolProperty(name = "Change",
                default = False,
                description = "change")

    grid : BoolProperty(
            name = "Grid",
            default = True,
            description = "Grid item?"
    )

    filepath : StringProperty(
            name = "Item File",
            default = ""
    )

    variant: EnumProperty(
                items=get_items,
                name="Variant",
                description="Pick a variant",
    )

    @classmethod
    def add_wall(cls, grid):
        pass

    def draw(self, context):
        global currentPath
        currentPath = self.filepath
        layout = self.layout
        box = layout.box()
        box.prop(self, "grid")
        box.prop(self, "variant")

    def execute(self, context):
        global currentPath
        currentPath = self.filepath
        if (self.filepath == ""):
            return {'Cancelled'}
        if (self.variant == None or len(self.variant) == 0):
            return {'FINISHED'}
        bpy.ops.import_scene.fbx(filepath = os.path.join(os.path.split(self.filepath)[0], self.variant))
        bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.object.transform_apply()
        if not self.grid:
            zoff = bpy.context.selected_objects[0].dimensions.z
            for o in context.selected_objects:
                o.location.z += zoff / 2
        bpy.ops.object.transform_apply()
        return {'FINISHED'}

def filen(fullpath):
    return os.path.split(fullpath)[1]

def filter_fbx(file):
    return (file.lower().endswith(".fbx"))

fullpath = icons_dir = os.path.join(os.path.dirname(__file__), TEMPLATE_DIR)
class VIEW3D_MT_TMTK_template_menu(Menu):
    bl_idname = "VIEW3D_MT_TMTK_template_menu"
    bl_label = "Templates"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        for menu in submenus:
            layout.menu(menu.bl_idname)


def submenu_draw(self, context):
    global currentPath
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'
    files = list(glob.iglob('**.fbx', root_dir = os.path.join(fullpath, self.subfolder), recursive=True))

    filtered = []
    for f in files:
        normalized = re.sub("_\dm.fbx", ".fbx", f)
        filtered.append(normalized)

    filtered = list(dict.fromkeys(sorted(filtered)))
    currentPath = self.subfolder
    for f in filtered:
        layout.operator(AddTMTKTemplate.bl_idname, text = f).filepath = os.path.join(fullpath, self.subfolder, f)

submenus = []
classTemplate = "VIEW3D_MT_TMTK_template_submenu_{}"

def init_module():
    global TMTKTEMPLATES_CLASSES
    subfolders = [f.name for f in os.scandir(fullpath) if f.is_dir()]
    for folder in subfolders:
        submenu = type(classTemplate + "basicshapes", (Menu,), {
            # data members
            "bl_idname": classTemplate.format(folder.replace(" ", "_")),
            "bl_label": folder,
            "subfolder": folder,

            # member functions
            "draw": submenu_draw
        })
        submenus.append(submenu)
    TMTKTEMPLATES_CLASSES += submenus

TMTKTEMPLATES_CLASSES = [
    VIEW3D_MT_TMTK_template_menu,
    AddTMTKTemplate
]

init_module()