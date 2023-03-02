"""
Copyright © 2023 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

bl_info = {
    "name": "TMTK Templates",
    "author": "Gohax",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Quickly add common templates used for TMTK",
    "warning": "",
    "category": "Add Mesh",
}

import bpy
from bpy.types import Menu
from . import add_tmtk_wall

class VIEW3D_MT_mesh_tmtk_add(Menu):
    # Define the "Single Vert" menu
    bl_idname = "VIEW3D_MT_mesh_tmtk_add"
    bl_label = "TMTK Wall"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.tmtk_wall_add",
                        text="Add TMTK wall template")

# Define "Extras" menu
def menu_func(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'

    layout.separator()
    self.layout.menu("VIEW3D_MT_mesh_tmtk_add",
                text="TMTK Objects")

def TMTK_context_menu(self, context):
    bl_label = 'Change'

    obj = context.object
    layout = self.layout

    if obj == None or obj.data is None:
        return

    if 'TMTKWall' in obj.data.keys():
        props = layout.operator("mesh.tmtk_wall_add", text="Change TMTK Wall")
        props.change = True
        for prm in add_tmtk_wall.WallParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

# Register
classes = [
    VIEW3D_MT_mesh_tmtk_add,
    add_tmtk_wall.AddTMTKWall,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # Add "Extras" menu to the "Add Mesh" menu and context menu.
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(TMTK_context_menu)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu and context menu.
    bpy.types.VIEW3D_MT_object_context_menu.remove(TMTK_context_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()