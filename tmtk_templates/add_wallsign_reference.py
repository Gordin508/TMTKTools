"""
Copyright © 2023 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import bpy
from bpy.types import Operator

class AddWallSignReference(Operator):
    bl_idname = "mesh.wallsign_reference"
    bl_label = "Add Wall Sign Reference"
    bl_description = "Add a reference to get the orientation of your wall sign right"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.row().label(text = "No options here, sorry", translate = False)

    def execute(self, context):
        if bpy.context.mode == "EDIT_MESH":
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.text_add(location=(0,0,0))
        text_obj = bpy.context.object
        text_obj.name = "Wall Sign Reference"

        text_obj.data.body = "Your sign\nshould\nbe oriented\nlike this"

        rotation_euler = text_obj.rotation_euler
        rotation_euler.rotate_axis("Z", 3.14159)
        text_obj.rotation_euler = rotation_euler
        text_obj.data.align_x = "CENTER"
        text_obj.data.align_y = "CENTER"
        text_obj.data.extrude = 0.05
        text_obj.location.z += 0.05

        return {'FINISHED'}