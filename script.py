import bpy
from mathutils import Vector
from mathutils import Matrix


class TMTKAnimationAdjuster(bpy.types.Operator):
    bl_idname = "object.tmtkanimationadjuster"
    bl_label = "TMTK Animation Adjuster"

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

    def get_override(self, area_type, region_type):
        for area in bpy.context.screen.areas:
            if area.type == area_type:
                for region in area.regions:
                    if region.type == region_type:
                        override = {'area': area, 'region': region}
                        return override
        #error message if the area or region wasn't found
        raise RuntimeError("Wasn't able to find", region_type," in area ", area_type,
                            "\n Make sure it's open while executing script.")

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
        bpy.ops.armature.select_all(action='SELECT')
        originalPivot = bpy.context.scene.tool_settings.transform_pivot_point
        originalCursorPos = bpy.context.scene.cursor.location
        bpy.context.scene.cursor.location = (0,0,0)
        bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
        #we need to override the context of our operator
        override = get_override( 'VIEW_3D', 'WINDOW' )

        bpy.ops.transform.rotate(override, value=-1.5708, orient_axis='X', orient_type='GLOBAL',
            orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False,
            use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1,
            use_proportional_connected=False, use_proportional_projected=False, snap=False,
            snap_elements={'VERTEX'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False,
            use_snap_edit=False, use_snap_nonedit=False, use_snap_selectable=False)
        bpy.ops.transform.resize(override, value=(100, 100, 100), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            orient_matrix_type='GLOBAL', mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH',
            proportional_size=1, use_proportional_connected=False, use_proportional_projected=False, snap=False,
            snap_elements={'VERTEX'}, use_snap_project=False, snap_target='CLOSEST', use_snap_self=False,
            use_snap_edit=False, use_snap_nonedit=False, use_snap_selectable=False)

        bpy.context.scene.cursor.location = originalCursorPos
        bpy.context.scene.tool_settings.transform_pivot_point = originalPivot


def menu_func(self, context):
    self.layout.operator(TMTKAnimationAdjuster.bl_idname, text=TMTKAnimationAdjuster.bl_label)

def register():
    bpy.utils.register_class(TMTKAnimationAdjuster)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister():
    bpy.utils.unregister_class(TMTKAnimationAdjuster)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
