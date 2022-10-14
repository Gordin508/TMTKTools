"""
Copyright © 2022 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import bpy
from mathutils import Matrix
import math
import re


bl_info = {
    "name": "TMTK Tools",
    "blender": (2, 80, 0),
    "location": "View3D > Object",
    "category": "Object",
    "author": "Gohax",
    "version": (0, 2),
    "description": "Tools to make TMTK item creation easier"
}

VERSION = bpy.app.version

class TMTKLODGenerator(bpy.types.Operator):
    bl_idname = "object.tmtklodoperator"
    bl_label = "TMTK Create LODs"
    bl_description = "Create LODs for selected objects"
    decimate: bpy.props.BoolProperty(name="Add decimate modifiers", description = "Add a preconfigured decimate modifier to each LOD level.",default=True)
    linkedcopies: bpy.props.BoolProperty(name="Create linked copies", description = "LODs reference the same mesh data as L0, as opposed to using deep copies.",default=False)
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (len([o for o in bpy.context.selected_objects if o.type == "MESH"]) > 0)

    def execute(self, context):
        meshObjects = [o for o in bpy.context.selected_objects if o.type == "MESH"]
        for obj in meshObjects:
            obj.name = re.sub("_L0$", "", obj.name)

            triangles = sum(len(polygon.vertices) - 2 for polygon in obj.data.polygons)
            minRatio = 64.0 / triangles
            for i in range (1,6):
                ratios = [0.8, 0.6, 0.4, 0.2, 0.1]
                new_obj = obj.copy()
                if (self.linkedcopies):
                    new_obj.data = obj.data
                else:
                    new_obj.data = obj.data.copy()
                new_obj.animation_data_clear()
                new_obj.name = obj.name + "_L{}".format(i)
                new_obj.hide_render = True
                for coll in obj.users_collection:
                    coll.objects.link(new_obj)
                if (self.decimate):
                    mod = new_obj.modifiers.new("LOD Decimator", "DECIMATE")
                    mod.ratio = ratios[i - 1] if ratios[i - 1] > minRatio else minRatio

            obj.name = obj.name + "_L0"

        if (len(meshObjects) == 1):
            self.report({'INFO'}, "Created LODs for {}".format(re.sub("_L0$", "", meshObjects[0].name)))
        else:
            self.report({'INFO'}, "Created LODs for {} objects".format(len(meshObjects)))
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

USE_VISIBLE_AVAILABLE = (VERSION[0] > 3 or (VERSION[0] >= 3 and VERSION[1] >= 2))
class TMTKExporter(bpy.types.Operator):
    bl_idname = "object.tmtkexporter"
    bl_label = "Export to FBX for TMTK"
    bl_description = "Export objects to FBX file with correct settings for TMTK"
    bl_options = {'REGISTER', 'UNDO'}
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255)
    onlySelected: bpy.props.BoolProperty(name="Export only selected objects", default=False)
    if (USE_VISIBLE_AVAILABLE):
        onlyVisible: bpy.props.BoolProperty(name="Export only visible objects", default=False)
    applyAnimationFix: bpy.props.BoolProperty(name="EXPERIMENTAL: Apply animation fix", default = False,
                                              description="Apply the TMTK animation fix to all armatures.")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if (len(self.filepath) > 0):
            if not (self.filepath.lower().endswith(".fbx")):
                self.filepath = self.filepath + ".fbx"
            exportArgs = {"filepath": self.filepath,
            "object_types": {"ARMATURE","MESH"},
            "bake_space_transform": True,
            "use_selection": self.onlySelected,
            "axis_forward": '-Z', "axis_up":'Y'}
            if (USE_VISIBLE_AVAILABLE):
                exportArgs["use_visible"] = self.onlyVisible
            if (self.applyAnimationFix):
                targetFilter = 1 + (self.onlySelected << 1) + ((not USE_VISIBLE_AVAILABLE or self.onlyVisible) << 2)
                bpy.ops.object.tmtkanimationfixer(targetSelection = targetFilter)
            self.report({'INFO'}, "Started FBX export")
            bpy.ops.export_scene.fbx(**exportArgs)
            self.report({'INFO'}, "Exported FBX to {}".format(self.filepath))
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


FIXEDPROP = "TMTKAnimFixed"
class TMTKAnimationFixer(bpy.types.Operator):
    bl_idname = "object.tmtkanimationfixer"
    bl_label = "TMTK Animation Fixer"
    bl_description = "Prepare animation for export to TMTK (only use directly before exporting)"
    bl_options = {'REGISTER', 'UNDO'}

    targetSelection: bpy.props.IntProperty(default = 0)

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type == "ARMATURE")

    def execute(self, context):
        if (self.targetSelection == 0):
            arma = bpy.context.active_object
            if (arma.type != "ARMATURE"):
                print("Active object is not of type Armature!")
                return {'CANCELLED'}
            else:
                if (arma.animation_data == None or arma.animation_data.action == None):
                    self.report({'WARNING'}, 'Operation cancelled as armature does not contain animation data')
                    return{'CANCELLED'}
                armaAction = arma.animation_data.action
                self.scaleLocationFcurves(armaAction)
                self.editArmature(arma)
        else:
            armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
            viewLayer = bpy.context.view_layer
            visibleFilter = ((self.targetSelection & 4) != 1)
            selectionFilter = ((self.targetSelection & 2) != 1)
            armafilter = lambda a: (visibleFilter == False or not a.hide_get(view_layer = viewLayer)) and (selectionFilter == False or a.select_get(view_layer = viewLayer))
            armaTargets = [a for a in armatures if armafilter(a)]
            for arma in armaTargets:
                self.processSilently(context, arma)
        return {'FINISHED'}

    def processSilently(self, context, armature: bpy.types.Object):
        assert(armature.type == "ARMATURE")
        if not (armature.get(FIXEDPROP) == True or armature.animation_data == None or armature.animation_data.action == None):
            armaAction = armature.animation_data.action
            self.scaleLocationFcurves(armaAction)
            self.editArmature(armature)

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
        armature["tmtk_animfixed"] = True

class TMTKSubMenu(bpy.types.Menu):
    bl_idname = 'object.tmtktools'
    bl_label = 'TMTK Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(TMTKAnimationFixer.bl_idname)
        layout.operator(TMTKLODGenerator.bl_idname)
        layout.operator(TMTKExporter.bl_idname)

def menu_func(self, context):
    self.layout.menu(TMTKSubMenu.bl_idname)

def register():
    bpy.utils.register_class(TMTKAnimationFixer)
    bpy.utils.register_class(TMTKLODGenerator)
    bpy.utils.register_class(TMTKExporter)
    bpy.utils.register_class(TMTKSubMenu)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(TMTKAnimationFixer)
    bpy.utils.unregister_class(TMTKExporter)
    bpy.utils.unregister_class(TMTKSubMenu)
    bpy.utils.unregister_class(TMTKLODGenerator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
