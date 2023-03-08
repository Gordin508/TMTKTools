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
from bpy.props import BoolProperty, StringProperty
from bpy_extras import object_utils
from bpy.utils import resource_path
import os

TEMPLATE_DIR = "templates"
ADDON_NAME = "shapes"

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

    @classmethod
    def add_wall(cls, grid):
        pass

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "grid")

    def execute(self, context):
        if (self.filepath == ""):
            return {'Cancelled'}
        bpy.ops.import_scene.fbx(filepath = self.filepath)
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
        layout.menu(VIEW3D_MT_TMTK_template_menu_basicswallhapes.bl_idname)

class VIEW3D_MT_TMTK_template_menu_basicswallhapes(Menu):
    bl_idname = "VIEW3D_MT_TMTK_template_menu_basicswallhapes"
    bl_label = "Basic Wall Shapes"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        self.path_menu([os.path.join(fullpath, "basic_walls")], AddTMTKTemplate.bl_idname, filter_ext = filter_fbx, display_name = filen)

TMTKTEMPLATES_CLASSES = [
    VIEW3D_MT_TMTK_template_menu_basicswallhapes,
    VIEW3D_MT_TMTK_template_menu,
    AddTMTKTemplate
]