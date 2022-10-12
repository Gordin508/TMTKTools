"""
Copyright © 2022 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import bpy
from mathutils import Vector
from mathutils import Matrix
import math

bl_info = {
    "name": "TMTK Tools",
    "blender": (3, 0, 0),
    "category": "Object",
}

class TMTKAnimationFixer(bpy.types.Operator):
    bl_idname = "object.tmtkanimationadfixer"
    bl_label = "TMTK Animation Fixer"

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type == "ARMATURE")

    def execute(self, context):
        arma = bpy.context.active_object

        if (arma.type != "ARMATURE"):
            print("Active object is not of type Armature!")
            return {'CANCELLED'}
        else:
            armaAction = arma.animation_data.action
            self.scaleLocationFcurves(armaAction)
            self.editArmature(arma)
            return {'FINISHED'}

    def scaleLocationFcurves(self, action : bpy.types.Action):
        for curve in action.fcurves:
            if (curve.data_path.__contains__("location")):
                for kfp in curve.keyframe_points:
                    kfp.co[1] *= 100.0
                    kfp.handle_left[1] *= 100.0
                    kfp.handle_right[1] *= 100.0

    def editArmature(self, armature : bpy.types.Object):
        assert(bpy.context.active_object.type == "ARMATURE")
        bpy.ops.object.mode_set(mode="EDIT")
        bones = armature.data.edit_bones;
        HALF_PI = math.pi / 2.0
        for bone in bones:
            transformMatrix = Matrix.Scale(100.0, 4) @ Matrix.Rotation(-HALF_PI, 4, 'X')
            bone.transform(transformMatrix)
        bpy.ops.object.mode_set(mode="OBJECT")

def menu_func(self, context):
    self.layout.operator(TMTKAnimationFixer.bl_idname, text=TMTKAnimationFixer.bl_label)

def register():
    bpy.utils.register_class(TMTKAnimationFixer)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(TMTKAnimationFixer)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
