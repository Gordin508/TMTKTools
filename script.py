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

"""
bl_info = {
    "name": "TMTK Tools",
    "blender": (3, 0, 0),
    "category": "Object",
    "version": (0, 1),
    "description": "Tools to make TMTK item creation easier"
}
"""

class TMTKLODGenerator(bpy.types.Operator):
    bl_idname = "object.lodoperator"
    bl_label = "TMTK Create LODs"

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type == "MESH")

    def execute(self, context):
        mesh = context.active_object
        if (mesh.name.endswith("_L0")):
            mesh.name = mesh.name.replace("_L0", "")

        triangles = sum(len(polygon.vertices) - 2 for polygon in  mesh.data.polygons)
        minRatio = 64.0 / triangles
        for i in range (1,6):
            ratios = [0.8, 0.6, 0.4, 0.2, 0.1]
            new_obj = mesh.copy()
            new_obj.data = mesh.data.copy()
            new_obj.animation_data_clear()
            new_obj.name = mesh.name + "_L{}".format(i)
            bpy.context.collection.objects.link(new_obj)
            mod = new_obj.modifiers.new("LOD Decimator", "DECIMATE")
            mod.ratio = ratios[i - 1] if ratios[i - 1] > minRatio else minRatio

        mesh.name = mesh.name + "_L0"
        return {'FINISHED'}


class TMTKAnimationFixer(bpy.types.Operator):
    bl_idname = "object.tmtkanimationfixer"
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

class TMTKSubMenu(bpy.types.Menu):
    bl_idname = 'object.tmtktools'
    bl_label = 'TMTK Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(TMTKAnimationFixer.bl_idname)
        layout.operator(TMTKLODGenerator.bl_idname)

def menu_func(self, context):
    self.layout.menu(TMTKSubMenu.bl_idname)

def register():
    bpy.utils.register_class(TMTKAnimationFixer)
    bpy.utils.register_class(TMTKLODGenerator)
    bpy.utils.register_class(TMTKSubMenu)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(TMTKAnimationFixer)
    bpy.utils.unregister_class(TMTKSubMenu)
    bpy.utils.unregister_class(TMTKLODGenerator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
