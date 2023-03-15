"""
Copyright © 2023 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

bl_info = {
    "name": "TMTK Templates",
    "author": "Gohax & Dada Poe",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Quickly add common templates used for TMTK",
    "warning": "",
    "category": "Add Mesh",
}

import bpy
from bpy.types import Menu
import os
from . import add_tmtk_wall
from . import tmtk_templates
from . import add_wallsign_reference

import bpy.utils.previews
icons_dict = []

classes = [
    add_tmtk_wall.AddTMTKWall,
    add_wallsign_reference.AddWallSignReference
]

def menu_func(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'

    layout.separator()
    layout.menu(tmtk_templates.VIEW3D_MT_TMTK_template_menu.bl_idname, text = "TMTK Template", icon_value = icons_dict['planco'].icon_id)
    layout.operator(add_tmtk_wall.AddTMTKWall.bl_idname, text="TMTK wall (generative)", icon_value = icons_dict['planco'].icon_id)
    layout.operator(add_wallsign_reference.AddWallSignReference.bl_idname, text="Wall sign reference", icon_value = icons_dict['planco'].icon_id)

def TMTK_context_menu(self, context):
    bl_label = 'Change'

    obj = context.object
    layout = self.layout

    if obj == None or obj.data is None:
        return

    if 'TMTKWall' in obj.data.keys():
        props = layout.operator(add_tmtk_wall.AddTMTKWall.bl_idname, text="Change TMTK Wall")
        props.change = True
        for prm in add_tmtk_wall.TMTKWallParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

def loadicon():
    global icons_dict
    icons_dict = bpy.utils.previews.new()
    icons_dir = os.path.dirname(__file__)
    icons_dict.load("planco", os.path.join(icons_dir, "icon.png"), 'IMAGE')

def register():
    from bpy.utils import register_class
    loadicon()
    allClasses = classes + tmtk_templates.TMTKTEMPLATES_CLASSES
    for cls in allClasses:
        register_class(cls)

    # Add "Extras" menu to the "Add Mesh" menu and context menu.
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(TMTK_context_menu)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu and context menu.
    bpy.types.VIEW3D_MT_object_context_menu.remove(TMTK_context_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    allClasses = classes + tmtk_templates.TMTKTEMPLATES_CLASSES
    from bpy.utils import unregister_class
    for cls in reversed(allClasses):
        unregister_class(cls)
    bpy.utils.previews.remove(icons_dict)

if __name__ == "__main__":
    register()