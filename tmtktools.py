"""
Copyright © 2023 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import bpy
from mathutils import Matrix
from mathutils import Vector
import os
import re


bl_info = {
    "name": "TMTK Tools",
    "blender": (2, 80, 0),
    "location": "View3D > Object",
    "category": "Object",
    "author": "Gohax",
    "version": (0, 2, 7),
    "description": "Tools to make TMTK item creation easier"
}

VERSION = bpy.app.version

TRIANGLE_LIMIT = 8000

def getTris(obj, deps=None):
    assert obj.type in HINTS_SUPPORTED_TYPES
    if deps is None:
        deps = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(deps)
    mesh = ev.data if obj.type == "MESH" else ev.to_mesh()
    mesh.calc_loop_triangles()
    return len(mesh.loop_triangles)

CONTEXT_TEMP_OVERWRITE_API = VERSION >= (4, 0, 0)
LOD_SUPPORTED_TYPES = ["MESH", "FONT", "CURVE"]
CAN_MOVE_MODIFIERS = "modifier_move_to_index" in dir(bpy.ops.object)
DECIMATE_BEFORE_ARMA_TOOLTIP = "If an armature modifier is present, move decimate modifier above it in the modifier stack (recommended)"
DECIMATE_BEFORE_ARMA_TOOLTIP_ALT = "Not available in this Blender version"
class TMTK_OT_LODGenerator(bpy.types.Operator):
    bl_idname = "tmtk.tmtklodoperator"
    bl_label = "TMTK: Create LODs"
    bl_description = "Create LODs for selected objects"
    decimate: bpy.props.BoolProperty(name="Add decimate modifiers", description = "Add a preconfigured decimate modifier to each LOD level",default=True)
    decimateBeforeArma: bpy.props.BoolProperty(name="Decimate before Armature",
                                               description = DECIMATE_BEFORE_ARMA_TOOLTIP if CAN_MOVE_MODIFIERS else DECIMATE_BEFORE_ARMA_TOOLTIP_ALT,
                                               default = CAN_MOVE_MODIFIERS)
    linkedcopies: bpy.props.BoolProperty(name="Create linked copies", description = "LODs reference the same mesh data as L0, as opposed to using deep copies",default=False)
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (len([o for o in bpy.context.selected_objects if o.type in LOD_SUPPORTED_TYPES]) > 0)

    def execute(self, context):
        meshObjects = [o for o in bpy.context.selected_objects if o.type in LOD_SUPPORTED_TYPES]
        for obj in meshObjects:
            obj.name = re.sub("_L0$", "", obj.name)
            triangles = getTris(obj)
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
                    modName = "LOD Decimator L{}".format(i)
                    mod = new_obj.modifiers.new(modName, "DECIMATE")
                    mod.ratio = ratios[i - 1] if ratios[i - 1] > minRatio else minRatio
                    armaMods = [i for i in range(0, len(new_obj.modifiers)) if new_obj.modifiers[i].type == "ARMATURE"]
                    if (self.decimateBeforeArma and len(armaMods) != 0):
                        if CONTEXT_TEMP_OVERWRITE_API:
                            from bpy import context
                            context_override = context.copy()
                            context_override['object'] = new_obj
                            with context.temp_override(**context_override):
                                bpy.ops.object.modifier_move_to_index(modifier = modName, index = armaMods[0])
                        else:
                            bpy.ops.object.modifier_move_to_index({'object': new_obj}, modifier = modName, index = armaMods[0])

            obj.name = obj.name + "_L0"

        if (len(meshObjects) == 1):
            self.report({'INFO'}, "Created LODs for {}".format(re.sub("_L0$", "", meshObjects[0].name)))
        else:
            self.report({'INFO'}, "Created LODs for {} objects".format(len(meshObjects)))
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        row = col.row()
        row.prop(self, "decimate")
        row = col.row()
        row.separator()
        row.prop(self, "decimateBeforeArma")
        row.enabled = self.decimate and CAN_MOVE_MODIFIERS
        row = col.row()
        row.prop(self, "linkedcopies")

FIXEDPROP = "TMTKAnimFixed"
USE_VISIBLE_AVAILABLE = (VERSION[0] > 3 or (VERSION[0] >= 3 and VERSION[1] >= 2))
class TMTK_OT_Exporter(bpy.types.Operator):
    bl_idname = "tmtk.tmtkexporter"
    bl_label = "TMTK: Export to FBX"
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
                                              description="Apply the TMTK animation fix to all armatures")
    addLeafBones: bpy.props.BoolProperty(name="Add Leaf Bones", default = False,
                                        description="Enable this if you intend to edit the armature from exported data")
    exportOther: bpy.props.BoolProperty(name="Export objects of type 'OTHER'", default = True,
                                        description="This includes curves and text objects, but not lights, cameras or empties")

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
            TMTK_OT_AnimationFixer.scaleLocationFcurves(armaAction, forward)
            TMTK_OT_AnimationFixer.prepareArmatureForExport(armature, forward)

    def execute(self, context):
        if (len(os.path.basename(self.filepath)) == 0):
            self.report({'WARNING'}, 'Cancelled FBX Export: Empty filename not allowed')
            return {'CANCELLED'}
        if not (self.filepath.lower().endswith(".fbx")):
            self.filepath = self.filepath + ".fbx"
        exportArgs = {"filepath": self.filepath,
        "object_types": {"ARMATURE","MESH", "OTHER"} if self.exportOther else {"ARMATURE","MESH"},
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


    def invoke(self, context, event):
        if (len(self.filepath) == 0):
            project_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            project_name = project_name if len(project_name) > 0 else "untitled"
            self.filepath = project_name + ".fbx"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class TMTK_OT_AnimationFixer(bpy.types.Operator):
    bl_idname = "tmtk.tmtkanimationfixer"
    bl_label = "TMTK: Animation Fixer"
    bl_description = "Prepare animation for export to TMTK (only use directly before exporting)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type == "ARMATURE")

    def execute(self, context):
        arma = bpy.context.active_object
        if (arma.type != "ARMATURE"):
            return {'CANCELLED'}
        else:
            if (arma.animation_data == None or arma.animation_data.action == None):
                self.report({'WARNING'}, 'Operation cancelled as armature does not contain animation data')
                return{'CANCELLED'}
            armaAction = arma.animation_data.action
            TMTK_OT_AnimationFixer.scaleLocationFcurves(armaAction)
            TMTK_OT_AnimationFixer.prepareArmatureForExport(arma)
            arma[FIXEDPROP] = True
        return {'FINISHED'}

    @classmethod
    def scaleLocationFcurves(cls, action : bpy.types.Action, forward = True):
        unitScale = bpy.context.scene.unit_settings.scale_length
        factor = (100.0 * unitScale) if forward else (0.01 / unitScale)
        for curve in action.fcurves:
            if (curve.data_path.__contains__("location")):
                for kfp in curve.keyframe_points:
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
        bones = armature.data.edit_bones
        unitScale = bpy.context.scene.unit_settings.scale_length
        scale = (100 * unitScale) if forward else (0.01 / unitScale)
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

MAXINFLUENCERS = 4
PRECISION = 12
class TMTK_OT_NormalizeWeights(bpy.types.Operator):
    bl_idname = "tmtk.tmtknormalizeoperator"
    bl_label = "TMTK: Normalize Bone Weights"
    bl_description = "Normalize Vertex Group Weights more precisely than Blender's Normalization would"
    bl_options = {'REGISTER', 'UNDO'}
    forceAll: bpy.props.BoolProperty(name="Re-Normalize all vertices", default = False,
                                        description="Do not check whether vertices are already normalized")
    applyMods: bpy.props.BoolProperty(name="Apply Modifiers", default = False,
                                        description="Permanently apply modifier stack before normalizing (except armature)")

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type == "MESH")

    def calculateSum(self, v):
        sum = 0.0
        for g in v.groups:
            sum += g.weight
        return sum

    def applyModifiers(self, obj):
        if (not self.applyMods or obj.type != "MESH" or len(obj.modifiers) == 0):
            return

        mods = [mod for mod in obj.modifiers if mod.type != "ARMATURE"]
        for mod in mods:
            bpy.ops.object.modifier_apply({'object': obj}, modifier = mod.name)

    def fixWeights(self, obj):
        fixedVerts = 0
        for v in obj.data.vertices:
            index = v.index
            if (len(v.groups) == 0):
                continue
            if (len(v.groups) > MAXINFLUENCERS):
                groupsSorted = sorted(v.groups, key = lambda g: g.weight, reverse = True)
                groupIDs = [g.group for g in groupsSorted[MAXINFLUENCERS:]]
                for gid in groupIDs:
                    obj.vertex_groups[gid].remove([v.index])

            v = obj.data.vertices[index]
            assert(len(v.groups) <= MAXINFLUENCERS)
            wsum = self.calculateSum(v)

            if (wsum == 1.0 and not self.forceAll):
                continue

            fixedVerts += 1

            for g in v.groups:
                newWeight = g.weight / wsum
                newWeight = int(newWeight * 2**PRECISION) * 2**(-PRECISION)
                g.weight = newWeight

            sortedIndices = sorted([i for i in range(0, len(v.groups))], key = lambda ind: v.groups[ind].weight, reverse = True)
            v.groups[sortedIndices[0]].weight = 1.0 - sum([v.groups[i].weight for i in sortedIndices[1:]])

            zeroGroups = [g.group for g in v.groups if g.weight == 0]
            for zgid in zeroGroups:
                obj.vertex_groups[zgid].remove([v.index])

        return fixedVerts

    def execute(self, context):
        foundUnapplied = False
        fixedVerts = 0
        warning = " Warning: At least one object had unapplied modifiers."
        selection = bpy.context.selected_objects
        for o in selection:
            if (o.type != "MESH"):
                continue
            if (self.applyMods):
                self.applyModifiers(o)
            if len([m for m in o.modifiers if m.type != "ARMATURE"]) > 0:
                foundUnapplied = True
            fixedVerts += self.fixWeights(o)
        if not (foundUnapplied):
            warning = ""
        self.report({'INFO'}, "Adjusted weights of {} vertices.{}".format(fixedVerts, warning))
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Make sure all relevant modifiers are applied.")
        row = col.row()
        row.prop(self, "forceAll")
        row.prop(self, "applyMods")


ICONS_AVAILABLE = bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys()
OKICON = "CHECKMARK" if "CHECKMARK" in ICONS_AVAILABLE else "CHECKBOX_HLT"
NOTOKICON = "ERROR" if "CHECKMARK" in ICONS_AVAILABLE else "CHECKBOX_DEHLT"
HINTS_SUPPORTED_TYPES = ["MESH", "FONT", "CURVE"]
class TMTK_OT_Hints(bpy.types.Operator):
    bl_idname = "tmtk.tmtkhints"
    bl_label = "TMTK: Hints"
    bl_description = "Give some hints about the currently selected object"

    @classmethod
    def poll(cls, context):
        return (context.active_object and bpy.context.active_object.type in HINTS_SUPPORTED_TYPES)

    def execute(self, context):
        return {'FINISHED'}

    def prepare(self, context):
        active = context.active_object
        self.meshname = re.sub("_L[0-5]$", "", active.name)
        self.lods = True
        self.lodTriCounts = []
        self.lodOrderError = -1
        self.type = active.type

        def getLod(name, i):
            return bpy.data.objects.get("{}_L{}".format(name, i))

        if active.type in HINTS_SUPPORTED_TYPES:
            deps = bpy.context.evaluated_depsgraph_get()
            for i in range(0,6):
                lod = getLod(self.meshname, i)
                if lod == None:
                    self.lods = False
                    break
                else:
                    self.lodTriCounts.append(getTris(lod, deps))
            if (self.lods):
                for i in range(0,5):
                    if (self.lodTriCounts[i + 1] > self.lodTriCounts[i]):
                        self.lodOrderError = i
            self.triCount = getTris(active, deps)
        else:
            self.lods = len([lod for lod in (getLod(self.meshname, i) for i in range(0,6)) if lod is not None]) == 6
            self.triCount = None
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

        def addText(box, text, isokay: bool = None, icon: str = None):
            kwargs = {"text": text, "translate": False}
            if isokay is not None:
                kwargs["icon"] = NOTOKICON if not isokay else OKICON
            if icon is not None:
                kwargs["icon"] = icon
            if "icon" in kwargs and kwargs["icon"] not in ICONS_AVAILABLE:
                del kwargs["icon"]
            box.row().label(**kwargs)

        box = layout.box()
        lodsokay = self.lods and self.lodOrderError < 0
        addText(box, "Object has LODs: {}".format(self.lods), isokay=lodsokay)
        if (self.lods):
            if (self.lodTriCounts and self.lodOrderError >= 0):
                e = self.lodOrderError
                addText(box, "- LODs are out of order: L{} ({} triangles) is less detailed than L{} ({} triangles)."
                                .format(e, self.lodTriCounts[e], e + 1, self.lodTriCounts[e + 1]))
            elif not self.lodTriCounts:
                addText(box,  "- Addon does not support checking for correct LOD order on objects of type {}".format(self.type))
        else:
            addText(box, "- You should add LODs named {} to {}".format(self.meshname + "_L0", self.meshname + "_L5"))

        box = layout.box()
        addText(box, "Object has assigned material: {}".format(self.hasMaterial), isokay=self.hasMaterial)
        if not (self.hasMaterial):
            addText(box, "- TMTK will refuse objects without any assigned material.")
        else:
            nameSuggestions = ", ".join([mat + "_BC.png" + ", " + mat + "_NM.png" for mat in self.materials])
            addText(box, "- Your texture files should be named {} etc.".format(nameSuggestions))

        box = layout.box()
        transformsapplied = not self.unappliedTransforms
        addText(box, "All object mode transformations are applied: {}".format(transformsapplied), isokay=transformsapplied)
        if (self.unappliedTransforms):
            addText(box, "- Unless this is intended, you should explicitly apply all object mode transformations before exporting.")

        box = layout.box()
        dimensionscorrect = not (self.tooSmall or self.tooLarge)
        addText(box, "Object has correct dimensions: {}".format(dimensionscorrect), isokay=dimensionscorrect)
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
        if self.triCount is not None:
            withinLimit = self.triCount <= TRIANGLE_LIMIT
            addText(box, "Object is within triangle limit ({}): {}".format(TRIANGLE_LIMIT, withinLimit), isokay=withinLimit)
            if (self.triCount > TRIANGLE_LIMIT):
                addText(box, "- Object has {} triangles".format(self.triCount, TRIANGLE_LIMIT))
        else:
            addText(box, "Object is within triangle limit ({}): {}".format(TRIANGLE_LIMIT, "N/A"))
            addText(box, "- Addon can not yet perform this check on objects of type {}".format(self.type))
        box = layout.box()
        addText(box, "Object is animated: {}".format(self.hasAnimation), icon="PAUSE" if not self.hasAnimation else "ARMATURE_DATA")
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


class TMTK_MT_TMTKMenu(bpy.types.Menu):
    bl_idname = 'TMTK_MT_tmtkmenu'
    bl_label = 'TMTK Tools'

    def draw(self, context):
        layout = self.layout
        layout.operator(TMTK_OT_AnimationFixer.bl_idname)
        layout.operator(TMTK_OT_LODGenerator.bl_idname)
        layout.operator(TMTK_OT_Exporter.bl_idname)
        layout.operator(TMTK_OT_Hints.bl_idname)
        layout.operator(TMTK_OT_NormalizeWeights.bl_idname)

def menu_func(self, context):
    self.layout.menu(TMTK_MT_TMTKMenu.bl_idname)

def register():
    bpy.utils.register_class(TMTK_OT_AnimationFixer)
    bpy.utils.register_class(TMTK_OT_LODGenerator)
    bpy.utils.register_class(TMTK_OT_Exporter)
    bpy.utils.register_class(TMTK_OT_Hints)
    bpy.utils.register_class(TMTK_OT_NormalizeWeights)
    bpy.utils.register_class(TMTK_MT_TMTKMenu)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(TMTK_OT_AnimationFixer)
    bpy.utils.unregister_class(TMTK_OT_LODGenerator)
    bpy.utils.unregister_class(TMTK_OT_Exporter)
    bpy.utils.unregister_class(TMTK_OT_Hints)
    bpy.utils.unregister_class(TMTK_OT_NormalizeWeights)
    bpy.utils.unregister_class(TMTK_MT_TMTKMenu)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
