"""
Copyright © 2022 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import bpy
from mathutils import Matrix
from mathutils import Vector
import math
import re


bl_info = {
    "name": "TMTK Tools",
    "blender": (2, 80, 0),
    "location": "View3D > Object",
    "category": "Object",
    "author": "Gohax",
    "version": (0, 2, 2),
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
            minRatio = minRatio if minRatio <= 1.0 else 1.0
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

FIXEDPROP = "TMTKAnimFixed"
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
    applyAnimationFix: bpy.props.BoolProperty(name="Apply animation fix", default = True,
                                              description="Apply the TMTK animation fix to all armatures.")
    addLeafBones: bpy.props.BoolProperty(name="Add Leaf Bones", default = False,
                                        description="Enable this if you intend to edit the armature from exported data")

    @classmethod
    def poll(cls, context):
        return True

    def getArmatures(self, context):
        armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
        viewLayer = bpy.context.view_layer
        visibleFilter = not USE_VISIBLE_AVAILABLE or self.onlyVisible
        selectionFilter = self.onlySelected
        armafilter = lambda a: ((a.get(FIXEDPROP) == True) or visibleFilter == False or not a.hide_get(view_layer = viewLayer)) and (selectionFilter == False or a.select_get(view_layer = viewLayer))
        armaTargets = [a for a in armatures if armafilter(a)]
        return armaTargets

    def processArmature(self, context, armature: bpy.types.Object, forward = True):
        assert(armature.type == "ARMATURE")
        if not (armature.get(FIXEDPROP) == True or armature.animation_data == None or armature.animation_data.action == None):
            armaAction = armature.animation_data.action
            TMTKAnimationFixer.scaleLocationFcurves(armaAction, forward)
            TMTKAnimationFixer.prepareArmatureForExport(armature, forward)

    def execute(self, context):
        if (len(self.filepath) > 0):
            if not (self.filepath.lower().endswith(".fbx")):
                self.filepath = self.filepath + ".fbx"
            exportArgs = {"filepath": self.filepath,
            "object_types": {"ARMATURE","MESH"},
            "bake_space_transform": True,
            "use_selection": self.onlySelected,
            "axis_forward": '-Z', "axis_up":'Y',
            "add_leaf_bones": self.addLeafBones}
            if (USE_VISIBLE_AVAILABLE):
                exportArgs["use_visible"] = self.onlyVisible
            if (self.applyAnimationFix):
                armatures = self.getArmatures(context)
                for arma in armatures:
                    self.processArmature(context, arma)
            self.report({'INFO'}, "Started FBX export")
            bpy.ops.export_scene.fbx(**exportArgs)
            if (self.applyAnimationFix):
                for arma in armatures:
                    self.processArmature(context, arma, forward = False)
            self.report({'INFO'}, "Exported FBX to {}".format(self.filepath))
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class TMTKAnimationFixer(bpy.types.Operator):
    bl_idname = "object.tmtkanimationfixer"
    bl_label = "TMTK Animation Fixer"
    bl_description = "Prepare animation for export to TMTK (only use directly before exporting)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type == "ARMATURE")

    def execute(self, context):
        arma = bpy.context.active_object
        if (arma.type != "ARMATURE"):
            print("Active object is not of type Armature!")
            return {'CANCELLED'}
        else:
            if (arma.animation_data == None or arma.animation_data.action == None):
                self.report({'WARNING'}, 'Operation cancelled as armature does not contain animation data')
                return{'CANCELLED'}
            armaAction = arma.animation_data.action
            TMTKAnimationFixer.scaleLocationFcurves(armaAction)
            TMTKAnimationFixer.prepareArmatureForExport(arma)
            arma[FIXEDPROP] = True
        return {'FINISHED'}

    @classmethod
    def scaleLocationFcurves(cls, action : bpy.types.Action, forward = True):
        for curve in action.fcurves:
            if (curve.data_path.__contains__("location")):
                for kfp in curve.keyframe_points:
                    factor = 100.0 if forward else 0.01
                    kfp.co[1] *= factor
                    kfp.handle_left[1] *= factor
                    kfp.handle_right[1] *= factor

    @classmethod
    def prepareArmatureForExport(cls, armature : bpy.types.Object, forward = True):
        assert(armature.type == "ARMATURE")
        originalSelected = bpy.context.selected_objects
        originalActive = bpy.context.view_layer.objects.active
        for selected in originalSelected:
            selected.select_set(False)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="EDIT")
        bones = armature.data.edit_bones;
        scale = 100 if forward else 0.01
        sign = -1 if forward else 1
        transformMatrix = Matrix([(scale,0,0,0),(0,0,-sign * scale,0),(0,sign * scale,0,0),(0,0,0,1)])
        PROPTY = "restore_Connect"
        for bone in bones:
            bone[PROPTY] = bone.use_connect
            bone.use_connect = False
        for bone in bones:
            bone.transform(transformMatrix)
        for bone in bones:
            bone.use_connect = bone[PROPTY]
            del bone[PROPTY]
        bpy.ops.object.mode_set(mode="OBJECT")
        armature.select_set(False)
        for selected in originalSelected:
            selected.select_set(True)
        bpy.context.view_layer.objects.active = originalActive

class TMTKHints(bpy.types.Operator):
    bl_idname = "object.tmtkhints"
    bl_label = "TMTK Hints"
    bl_description = "Give some hints about the currently selected object"

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type == "MESH")

    def execute(self, context):
        return {'FINISHED'}

    def prepare(self, context):
        active = context.active_object
        self.meshname = re.sub("_L[0-5]$", "", active.name)
        self.lods = True
        self.lodTriCounts = []
        deps = bpy.context.evaluated_depsgraph_get()
        for i in range(0,6):
            lod = bpy.data.objects.get("{}_L{}".format(self.meshname, i))
            if lod == None:
                self.lods = False
                break
            else:
                eval = lod.evaluated_get(deps)
                eval.data.calc_loop_triangles()
                self.lodTriCounts.append(len(eval.data.loop_triangles))
        self.lodOrderError = -1
        if (self.lods):
            for i in range(0,5):
                if (self.lodTriCounts[i + 1] > self.lodTriCounts[i]):
                    self.lodOrderError = i
        selfEval = active.evaluated_get(deps)
        selfEval.data.calc_loop_triangles()
        self.triCount = len(selfEval.data.loop_triangles)
        materialSlots = [slot for slot in active.material_slots if slot.material != None]
        self.hasMaterial = (len(materialSlots) > 0)
        self.materials = [slot.material.name for slot in materialSlots]
        self.hasAnimation = (active.find_armature() != None)
        self.hasArmatureModifier = len([mod for mod in active.modifiers if mod.type == "ARMATURE"])

        UNITYVECTOR = Vector((1, 1, 1))
        ZEROVECTOR = Vector((0, 0, 0))
        mode = active.rotation_mode
        self.unappliedTransforms = False
        if (mode == "QUATERNION"):
            self.unappliedTransforms = self.unappliedTransforms or active.rotation_quaternion != Vector((1, 0, 0 ,0))
        else:
            euler = active.rotation_euler
            self.unappliedTransforms = self.unappliedTransforms or Vector((euler.x, euler.y, euler.z)) != ZEROVECTOR
        self.unappliedTransforms = self.unappliedTransforms or (active.scale != UNITYVECTOR or active.location != ZEROVECTOR)

        self.unit_scale = bpy.context.scene.unit_settings.scale_length
        self.dimensions = active.dimensions * self.unit_scale
        self.tooLarge = (max(self.dimensions) > 8.0)
        self.tooSmall = (max(self.dimensions) < 0.5 or min(self.dimensions) < 0.01)

    def draw(self, context):
        layout = self.layout
        addText = lambda box, string: box.row().label(text = string, translate = False)
        box = layout.box()
        addText(box, "Object has LODs: {}".format(self.lods))
        if (self.lods):
            if (self.lodOrderError >= 0):
                e = self.lodOrderError
                addText(box, "- LODs are out of order: L{} ({} triangles) is less detailed than L{} ({} triangles)."
                                .format(e, self.lodTriCounts[e], e + 1, self.lodTriCounts[e + 1]))
        else:
            addText(box, "- You should add LODs named {} to {}".format(self.meshname + "_L0", self.meshname + "_L5"))

        box = layout.box()
        addText(box, "Object has assigned material: {}".format(self.hasMaterial))
        if not (self.hasMaterial):
            addText(box, "- TMTK will refuse objects without any assigned material.")
        else:
            nameSuggestions = ", ".join([mat + "_BC.png" + ", " + mat + "_NM.png" for mat in self.materials])
            addText(box, "- Your texture files should be named {} etc.".format(nameSuggestions))

        box = layout.box()
        addText(box, "All object mode transformations are applied: {}".format(not self.unappliedTransforms))
        if (self.unappliedTransforms):
            addText(box, "- Unless this is intended, you should explicitly apply all object mode transformations before exporting.")

        box = layout.box()
        addText(box, "Object has correct dimensions: {}".format(not(self.tooSmall or self.tooLarge)))
        if (self.tooSmall or self.tooLarge):
            addText(box, "- Object dimensions: {:0.3f}m, {:0.3f}m, {:0.3f}m (x, y, z)".format(self.dimensions[0], self.dimensions[1], self.dimensions[2]))
        if (self.unit_scale != 1.0):
            addText(box, "- Info: Scene unit scale is {:0.2f}".format(self.unit_scale))
        if (self.tooSmall):
            addText(box, "- Smallest axis is under 0.01m or largest is under 0.5m")
            addText(box, "- This warning may be irrelevant if you intend to combine multiple objects.")
        if (self.tooLarge):
            addText(box, "- Longest axis is over 8.0m")

        box = layout.box()
        addText(box, "Object fulfills triangle limit: {}".format(self.triCount <= 8000))
        if (self.triCount > 8000):
            addText(box, "Object has {} triangles (allowed: {})".format(self.triCount, 8000))
        box = layout.box()
        addText(box, "Object is animated: {}".format(self.hasAnimation))
        if (self.hasAnimation):
            addText(box, "- Make sure to use the animation fixes when exporting")
            if (self.hasArmatureModifier):
                addText(box, "- You are using an armature modifier for parenting, which is correct.")
                addText(box, "- Make sure to create your keyframes in pose mode.")
            else:
                addText(box, "- You are not using an armature modifier. Your animation will probably not work ingame.")


    def invoke(self, context, event):
        self.prepare(context)
        context.window_manager.invoke_popup(self, width=700)
        return {'RUNNING_MODAL'}


class TMTKSubMenu(bpy.types.Menu):
    bl_idname = 'object.tmtktools'
    bl_label = 'TMTK Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(TMTKAnimationFixer.bl_idname)
        layout.operator(TMTKLODGenerator.bl_idname)
        layout.operator(TMTKExporter.bl_idname)
        layout.operator(TMTKHints.bl_idname)

def menu_func(self, context):
    self.layout.menu(TMTKSubMenu.bl_idname)

def register():
    bpy.utils.register_class(TMTKAnimationFixer)
    bpy.utils.register_class(TMTKLODGenerator)
    bpy.utils.register_class(TMTKExporter)
    bpy.utils.register_class(TMTKHints)
    bpy.utils.register_class(TMTKSubMenu)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(TMTKAnimationFixer)
    bpy.utils.unregister_class(TMTKLODGenerator)
    bpy.utils.unregister_class(TMTKExporter)
    bpy.utils.unregister_class(TMTKHints)
    bpy.utils.unregister_class(TMTKSubMenu)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
