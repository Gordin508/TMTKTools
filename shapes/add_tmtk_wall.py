"""
Copyright © 2023 Gohax

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import bpy
from bpy.types import Operator
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty
from bpy_extras import object_utils

def create_mesh_object(context, self, verts, edges, faces, name):

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    return object_utils.object_data_add(context, mesh, operator=self)


class AddTMTKWall(Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.tmtk_wall_add"
    bl_label = "Add TMTK Wall"
    bl_description = "Add a wall conforming to Planet Coaster's dimensions"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    change : BoolProperty(name = "Change",
                default = False,
                description = "change wall")
    height: FloatProperty(
        name="Wall Height",
        description="Height of the wall",
        min=0.25,
        max=8.0,
        default=4.0
    )

    width: FloatProperty(
        name="Wall Width",
        description="Width of the wall",
        min=0.5,
        max=8.0,
        default=4.0
    )

    grid : BoolProperty(
            name = "Grid",
            default = True,
            description = "Grid item?"
    )

    @classmethod
    def add_wall(cls, height, width, grid):
        depth2 = 0.375 / 2
        width2 = width / 2
        verts = []
        verts += [Vector((-width2, depth2, 0.0)), Vector((-width2, depth2, height))]
        verts += [Vector((width2, depth2, 0.0)), Vector((width2, depth2, height))]
        verts += [Vector((width2, -depth2, 0.0)), Vector((width2, -depth2, height))]
        verts += [Vector((-width2, -depth2, 0.0)), Vector((-width2, -depth2, height))]

        faces = [[i % 8 for i in range(j, j+4)] for j in range(0,8,2)]
        faces = [[a,b,d,c] for [a,b,c,d] in faces]
        faces += [[i % 8 for i in range(0,8)[::2]]]
        faces += [[i % 8 for i in range(0,8)[::-2]]]

        if (grid):
            for v in verts:
                v.z -= height / 2.0
        return verts, faces

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "height")
        box.prop(self, "width")
        box.prop(self, "grid")

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False
        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('TMTKWall' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name

                verts, faces = AddTMTKWall.add_wall(self.height, self.width, self.grid)
                mesh = bpy.data.meshes.new("TMP")
                mesh.from_pydata(verts, [], faces)
                mesh.update()
                obj.data = mesh

                for material in oldmesh.materials:
                    obj.data.materials.append(material)

                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                verts, faces = AddTMTKWall.add_wall(self.height, self.width, self.grid)
                obj = create_mesh_object(context, self, verts, [], faces, "Wall")
            obj.data["TMTKWall"] = True
            obj.data["change"] = False
            for prm in TMTKWallParameters():
                obj.data[prm] = getattr(self, prm)
        
        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            verts, faces = AddTMTKWall.add_wall(self.height, self.width, self.grid)

            obj = create_mesh_object(context, self, verts, [], faces, "TMP")

            obj.select_set(True)
            active_object.select_set(True)
            bpy.context.view_layer.objects.active = active_object
            bpy.ops.object.join()
            context.active_object.name = name_active_object
            bpy.ops.object.mode_set(mode='EDIT')


        if use_enter_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')
        # restore pre operator state
        bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

        return {'FINISHED'}



def TMTKWallParameters():
    TMTKWallParameters = [
        "height",
        "width",
        "grid",
    ]
    return TMTKWallParameters