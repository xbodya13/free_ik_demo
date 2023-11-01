from typing import *

bl_info={
    "name":"FREEIK DEMO",
    "category":"Rigging",
    "version":(1,1,7),
    "blender":(4,0,0),
    "location":"",
    "description":"Demo version of more intuitive way to rig and animate",
    "wiki_url":"https://xbodya13.github.io/free_ik_doc/",
    "tracker_url":"https://github.com/xbodya13/free_ik_doc/issues"
}

import itertools
import bpy
# import bgl
import gpu
from gpu_extras.batch import batch_for_shader
import mathutils
import time
import numpy as np
import random
# import os

import rna_prop_ui

import math
from bpy.app.handlers import persistent


class gv:
    prime_name="free_ik"

    constrait_group_name=prime_name+"_constraint_collection"

    nodes=[]  #type: List[Node]
    clustered_nodes=[]  #type: List[Node]
    links=[]  #type: List[Link]
    clusters=[]  #type: List[Cluster]

    nodes_dictionary={}  #type: Dict[Node]
    links_dictionary={}  #type: Dict[Link]

    links_changed=False
    transform_changed=False
    last_group_state=[]
    last_group_length=0

    time_to_force_rebuild=False
    time_to_update_drivers=False
    time_to_force_solve=False

    is_frame=False

    is_translating=False
    is_rotating=False
    is_scaling=False
    is_transforming=False
    is_graph_changing=False

    operator_changed=False

    is_pose_library=False
    is_pose_paste=False
    is_paste_selected_only=False
    is_paste_mirrored=False
    is_clear_pose=False
    is_clear_translation=False
    is_clear_rotation=False
    is_clear_scale=False
    is_after_frame=False
    is_key_delete=False
    is_key_create=False
    is_flip_quaternion=False
    is_rendering=False
    is_curve_change=False
    is_modal_transform=False
    is_nla_modal=False
    is_reference_update=False
    was_clear_pose=False
    was_clear_translation=False
    was_clear_rotation=False
    was_clear_scale=False
    was_delete=False

    is_indirect_key_create=False



    is_playback=False
    was_playback=False
    playback_stopped=False


    force_update=False

    is_armature_shift=False

    inherit_location=False
    inherit_rotation=False
    inherit_scale=False
    inherit_any=False

    use_individual_origins=False


    is_modal=False

    last_operator=None
    last_frame_operator=None
    last_mode=None
    modal_start_operator=None
    active_operator=None

    shift_by_operator=False

    smooth='SMOOTH'
    rope='ROPE'
    stretch='STRETCH'
    solver_mode=smooth

    stretch_head='STRETCH_HEAD'
    stretch_tail='STRETCH_TAIL'
    stretch_both='STRETCH_BOTH'
    stretch_mode=stretch_both

    scene_iterations=None
    frame_iterations=None




    limit_location_name=prime_name+"_limit_location"
    limit_rotation_name=prime_name+"_limit_rotation"
    limit_scale_name=prime_name+"_limit_scale"

    pose_parent_name=prime_name+"_pose_parent"
    frame_parent_name=prime_name+"_frame_parent"

    skip=False

    time_to_make_keys=False

    translate_name='transform.translate'
    rotate_name='transform.rotate'
    resize_name='transform.resize'
    bend_name='transform.bend'
    to_sphere_name='transform.tosphere'
    shear_name='transform.shear'
    mirror_name='transform.mirror'
    copy_pose_name='pose.copy'
    paste_pose_name='pose.paste'

    keymap=None

    shader=gpu.shader.from_builtin('SMOOTH_COLOR')

    shader.bind()

    keyconfig=None
    keymaps=None

    #CAUSES
    transform_operator="TRANSFORM OPERATOR"
    nla_transform_operator="NLA TRANSFORM OPERATOR"
    clear_pose_operator="CLEAR POSE OPERATOR"
    paste_pose_operator="PASTE POSE OPERATOR"

    fade=1

    id_object_cluster_dictionary={}
    id_object_animation_dictionary={}
    id_object_state_dictionary={}




class FreeIKNodeSettings(bpy.types.PropertyGroup):
    node_a_name=gv.prime_name+"_node_a"
    node_b_name=gv.prime_name+"_node_b"

    def get_node(self,name):
        try:
            holder=self.id_data.constraints[name]
            if type(holder.target.data)==bpy.types.Armature and holder.subtarget!="":
                return holder.target.pose.bones[holder.subtarget]
            else:
                return holder.target
        except:
            return None

    def set_node(self,other,name):
        try:
            if name in self.id_data.constraints:
                holder=self.id_data.constraints[name]
            else:
                holder=self.id_data.constraints.new(type='CHILD_OF')
                holder.name=name
                holder.mute=True

            if type(other)==bpy.types.PoseBone:
                holder.target,holder.subtarget=other.id_data,other.name
            else:
                holder.target=other
        except:
            pass

    def get_node_a(self):
        return self.get_node(self.node_a_name)

    def set_node_a(self,other):
        self.set_node(other,self.node_a_name)

    node_a=property(get_node_a,set_node_a)

    def get_node_b(self):
        return self.get_node(self.node_b_name)

    def set_node_b(self,other):
        self.set_node(other,self.node_b_name)

    node_b=property(get_node_b,set_node_b)

    def get_picker_a(self):
        try:
            return self.id_data.constraints[self.node_a_name]
        except:
            return None

    node_a_picker=property(get_picker_a)

    def get_picker_b(self):
        try:
            return self.id_data.constraints[self.node_b_name]
        except:
            return None

    node_b_picker=property(get_picker_b)

    point_a: bpy.props.FloatVectorProperty(name="Local point")
    point_b: bpy.props.FloatVectorProperty(name="Local point")




    is_pinned: bpy.props.BoolProperty(name="Pinned",default=False,options={'ANIMATABLE'})
    is_enabled: bpy.props.BoolProperty(name="Enabled",default=True)

    priority: bpy.props.IntProperty(name="Priority",default=0)

    limit_location: bpy.props.FloatVectorProperty(name="Limit location",subtype='TRANSLATION',size=3)
    limit_rotation: bpy.props.FloatVectorProperty(name="Limit rotation",subtype='EULER',size=3)
    limit_scale: bpy.props.FloatVectorProperty(name="Limit scale",subtype='XYZ',size=3)

    is_rig_enabled: bpy.props.BoolProperty(name="Enabled",default=True)



    color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', size=3,default=bpy.context.preferences.themes[0].view_3d.bone_solid)
    pinned_color: bpy.props.FloatVectorProperty(name="Pinned color", subtype='COLOR', size=3, default=(1, 0, 0))



class FreeIKConstraintPanel(bpy.types.Panel):
    bl_idname="OBJECT_PT_free_ik_constraint_panel"
    bl_label="FreeIK constraint"
    bl_space_type='PROPERTIES'
    bl_region_type='WINDOW'
    bl_context="object"

    @classmethod
    def poll(self,context):
        if None not in (context.object.free_ik.node_a_picker,context.object.free_ik.node_b_picker):
            return True

        else:
            return False

    def draw_node(self,layout,picker,text):
        layout.prop(picker,"target",text=text)
        if picker.target is not None:
            if type(picker.target.data)==bpy.types.Armature:
                layout.prop_search(picker,"subtarget",picker.target.pose,"bones",text="Bone")

    def draw(self,context):
        layout=self.layout

        layout.prop(context.object.free_ik,"is_enabled")

        column=layout.column()
        self.draw_node(column,context.object.free_ik.node_a_picker,"Object A")
        column.prop(context.object.free_ik,"point_a")
        self.draw_node(column,context.object.free_ik.node_b_picker,"Object B")
        column.prop(context.object.free_ik,"point_b")


def solve_enable_update(self,context):
    set_limits_state(self.enable_solver)


class FreeIKSceneSettings(bpy.types.PropertyGroup):
    group: bpy.props.PointerProperty(type=bpy.types.Collection)

    enable_solver: bpy.props.BoolProperty(name="Enable solver",default=True,update=solve_enable_update)

    scene_iterations: bpy.props.IntProperty(name="Posing iterations",default=20)
    frame_iterations: bpy.props.IntProperty(name="Playback iterations",default=5)

    inherit_location: bpy.props.BoolProperty(name="Inherit location",default=True)
    inherit_rotation: bpy.props.BoolProperty(name="Inherit rotation",default=True)
    inherit_scale: bpy.props.BoolProperty(name="Inherit scale",default=True)

    # show_overlays:bpy.props.BoolProperty(name="FreeIK",default=True)
    show_generic: bpy.props.BoolProperty(name="Generic",default=True)
    show_pinned: bpy.props.BoolProperty(name="Pinned",default=True)


    solver_mode: bpy.props.EnumProperty(name="Posing mode",
                                 items=[
                                     (gv.smooth,"","",'NONE',0),
                                     (gv.rope,"","",'NONE',1),
                                     (gv.stretch,"","",'NONE',2),

                                 ]
                                 )
    stretch_mode: bpy.props.EnumProperty(name="Stretch mode",
                                 items=[
                                     (gv.stretch_both,"","",'NONE',0),
                                     (gv.stretch_head,"","",'NONE',1),
                                     (gv.stretch_tail,"","",'NONE',2),
                                 ]
                                 )


class FreeIKScenePanel(bpy.types.Panel):
    bl_idname="SCENE_PT_free_ik_scene_panel"
    bl_label="Free IK world"
    bl_space_type='PROPERTIES'
    bl_region_type='WINDOW'
    bl_context="scene"

    @classmethod
    def poll(self,context):
        return True

    def draw(self,context):
        layout=self.layout
        # layout.prop(context.scene.free_ik.group_picker,f'["{FreeIKSceneSettings.group_name}"]',text="Constraint group")
        layout.prop(context.scene.free_ik,"group",text="Constraint group")

        layout.prop(context.scene.free_ik,"enable_solver")
        layout.prop(context.scene.free_ik,"scene_iterations")
        layout.prop(context.scene.free_ik,"frame_iterations")


def draw_parent(layout,item,constraint_name,text):
    if constraint_name in item.constraints:
        picker=item.constraints[constraint_name]

        layout.separator()
        layout.prop(picker,"target",text=text)
        if picker.target is not None:
            if type(picker.target.data)==bpy.types.Armature:
                layout.prop_search(picker,"subtarget",picker.target.pose,"bones",text="Bone")


class FreeIKObjectPanel(bpy.types.Panel):
    bl_idname="OBJECT_PT_free_ik_object_panel"
    bl_label="FreeIK node"
    bl_space_type='PROPERTIES'
    bl_region_type='WINDOW'
    bl_context="object"

    @classmethod
    def poll(self,context):
        if context.object in gv.nodes_dictionary:
            return True
        else:
            return False

    def draw(self,context):
        layout=self.layout
        layout.prop(context.object,"free_ik_is_pinned")
        draw_parent(layout,context.object,gv.pose_parent_name,"Pose parent")
        draw_parent(layout,context.object,gv.frame_parent_name,"Playback parent")
        layout.prop(context.object,"free_ik_stretch_factor")
        layout.prop(context.object.free_ik, "color")
        layout.prop(context.object.free_ik, "pinned_color")


class FreeIKBonePanel(bpy.types.Panel):
    bl_idname="OBJECT_PT_free_ik_bone_panel"
    bl_label="FreeIK node"
    bl_space_type='PROPERTIES'
    bl_region_type='WINDOW'
    bl_context="bone"

    @classmethod
    def poll(self,context):
        if context.active_pose_bone in gv.nodes_dictionary:
            return True
        else:
            return False

    def draw(self,context):
        layout=self.layout
        layout.prop(context.active_pose_bone,"free_ik_is_pinned")
        draw_parent(layout,context.active_pose_bone,gv.pose_parent_name,"Pose parent")
        draw_parent(layout,context.active_pose_bone,gv.frame_parent_name,"Playback parent")
        layout.prop(context.active_pose_bone,"free_ik_stretch_factor")

        layout.prop(context.active_pose_bone.free_ik, "color")
        layout.prop(context.active_pose_bone.free_ik, "pinned_color")


class LinkState:
    def __init__(self):
        self.point_a=mathutils.Vector((0.0,0.0,0.0))
        self.point_b=mathutils.Vector((0.0,0.0,0.0))
        self.points=(self.point_a,self.point_b)
        self.is_enabled=None


class Link:

    def __init__(self,constraint):
        self.source=constraint
        self.source_name=self.source.name

        self.node_a=self.source.free_ik.node_a  #type:Node
        self.node_b=self.source.free_ik.node_b  #type:Node
        self.nodes=None  #type: List[Node]

        self.point_a=mathutils.Vector((0.0,0.0,0.0))
        self.point_b=mathutils.Vector((0.0,0.0,0.0))
        self.point_a[:]=self.source.free_ik.point_a[:]
        self.point_b[:]=self.source.free_ik.point_b[:]

        self.points=(self.point_a,self.point_b)

        self.origin_a=None
        self.origin_b=None

        self.node=self.node_a
        self.other_node=self.node_b

        self.point=self.point_a
        self.other_point=self.point_b

        self.origin=None
        self.other_origin=None

        self.length=0
        self.error=0

        self.update_origins=False

        self.is_enabled=self.source.free_ik.is_enabled

        self.is_used=False

        self.is_line=False
        self.is_simple=False

        self.cluster=None  #type: Cluster

        self.last_state=LinkState()

        self.read_state()

    # def __hash__(self):
    #     return id(self)
    #
    # def __eq__(self, other):
    #     return (self.node_a is other.node_a and self.node_b is other.node_b) or (self.node_a is other.node_b and self.node_b is other.node_a)
    #

    def __str__(self):
        # return f"LINK {self.source.name}  {self.node_a.source.name}<->{self.node_b.source.name}"

        return f"LINK {self.source.name}"

    def __repr__(self):
        return self.__str__()

    def restore_from_name(self):
        self.source=bpy.data.objects[self.source_name]

    def restore_name(self):
        self.source_name=self.source.name

    def is_twin(self,other):
        return (self.node_a is other.node_a and self.node_b is other.node_b) or (self.node_a is other.node_b and self.node_b is other.node_a)


    def read_state(self):
        self.is_enabled=self.source.free_ik.is_enabled
        self.last_state.is_enabled=self.is_enabled


        self.point_a[:],self.point_b[:]=self.source.free_ik.point_a[:],self.source.free_ik.point_b[:]

        self.last_state.point_a[:]=self.point_a[:]
        self.last_state.point_b[:]=self.point_b[:]

    def update_state_from_other(self,source):
        self.is_enabled=source.free_ik.is_enabled


    def update_state_frame(self):
        self.is_enabled=self.source.free_ik.is_enabled
        if self.is_enabled!=self.last_state.is_enabled:
            gv.links_changed=True
        self.last_state.is_enabled=self.is_enabled

    def update_state_scene(self):
        self.is_enabled=self.source.free_ik.is_enabled
        if self.is_enabled!=self.last_state.is_enabled:
            gv.links_changed=True
        self.last_state.is_enabled=self.is_enabled

        self.point_a[:],self.point_b[:]=self.source.free_ik.point_a[:],self.source.free_ik.point_b[:]

        if self.is_enabled and self.cluster is not None:

            for point,last_point,node in zip(self.points,self.last_state.points,self.nodes):
                if point!=last_point:
                    for link in node.links:
                        if link is not self: link.update_origins=True
                    self.cluster.points_changed=True

        self.last_state.point_a[:]=self.point_a[:]
        self.last_state.point_b[:]=self.point_b[:]

    def update_length(self):
        self.length=((self.node_a.matrix@self.origin_a-self.node_a.matrix@self.point_a).length+(
                    self.node_b.matrix@self.origin_b-self.node_b.matrix@self.point_b).length)*0.5

    def get_error(self):
        # pass#print("LENGTH ",self.node_a.matrix@self.point_a-self.node_b.matrix@self.point_b)
        # pass#print(self.node_a.matrix)
        # pass#print(self.node_b.matrix)
        if self.length==0:
            return 0
        else:
            return (self.node_a.matrix@self.point_a-self.node_b.matrix@self.point_b).length/self.length

    def get_length(self):
        return (self.node_a.matrix@self.point_a-self.node_b.matrix@self.point_b).length

    def make_origins(self):

        origins=[]

        for node,point in zip(self.nodes,self.points):

            max_length=0
            max_point=None

            if len(node.points)>=2:
                for node_point in node.points:
                    length=(point-node_point).length
                    if max_point is None or length>max_length:
                        max_length=length
                        max_point=node_point
                origins.append(max_point)

            else:
                for node_point in node.fallback_points:
                    length=(point-node_point).length
                    if max_point is None or length>max_length:
                        max_length=length
                        max_point=node_point
                origins.append(max_point)

        pass  #print(origins)

        self.origin_a,self.origin_b=origins



    def get_origins(self,work_nodes):

        origins=[]

        for node,point in zip(self.nodes,self.points):

            max_length=0
            max_point=None


            for node_point,linked_node in zip(node.points,node.linked_nodes):
                if linked_node in work_nodes:
                    length=(point-node_point).length
                    if max_point is None or length>max_length:
                        max_length=length
                        max_point=node_point



            if max_point is None:
                for node_point in node.fallback_points:
                    length=(point-node_point).length
                    if max_point is None or length>max_length:
                        max_length=length
                        max_point=node_point
                origins.append(max_point)

            else:
                origins.append(max_point)


        return origins


    def set_active(self,node):
        if node is self.node_a:
            self.node=self.node_a
            self.other_node=self.node_b
            self.point=self.point_a
            self.other_point=self.point_b
            self.origin=self.origin_a
            self.other_origin=self.origin_b
        else:
            self.node=self.node_b
            self.other_node=self.node_a
            self.point=self.point_b
            self.other_point=self.point_a
            self.origin=self.origin_b
            self.other_origin=self.origin_a



    def track_to(self,target=None,only_translate=False):
        if target is None:
            target_world=(self.node_a.matrix@self.point_a+self.node_b.matrix@self.point_b)/2
            to_point(self.node_a.matrix,self.point_a,self.origin_a,target_world,only_translate=self.node_a.is_only_translated or only_translate)
            to_point(self.node_b.matrix,self.point_b,self.origin_b,target_world,only_translate=self.node_b.is_only_translated or only_translate)

        elif target is self.node_a :
            to_point(self.node_b.matrix,self.point_b,self.origin_b,self.node_a.matrix@self.point_a,only_translate=self.node_b.is_only_translated or only_translate)
        elif target is self.node_b :
            to_point(self.node_a.matrix,self.point_a,self.origin_a,self.node_b.matrix@self.point_b,only_translate=self.node_a.is_only_translated or only_translate)


    def scale_to(self,target=None):
        if target is None:
            target_world=(self.node_a.matrix@self.point_a+self.node_b.matrix@self.point_b)/2
            to_point_scale(self.node_a.matrix,self.point_a,self.origin_a,target_world,self.node_a.stretch_factor)
            to_point_scale(self.node_b.matrix,self.point_b,self.origin_b,target_world,self.node_b.stretch_factor)

        elif target is self.node_a :
            to_point_scale(self.node_b.matrix,self.point_b,self.origin_b,self.node_a.matrix@self.point_a,self.node_b.stretch_factor)
        elif target is self.node_b :
            to_point_scale(self.node_a.matrix,self.point_a,self.origin_a,self.node_b.matrix@self.point_b,self.node_a.stretch_factor)





    def get_angle(self):
        va=self.node_a.matrix@self.origin_a-self.node_a.matrix@self.point_a
        vb=self.node_b.matrix@self.origin_b-self.node_b.matrix@self.point_b
        fallback=0
        return va.angle(vb,fallback)

    def set_angle(self,target_angle=0):
        matrix_a=self.node_a.matrix
        matrix_b=self.node_b.matrix

        va=self.node_a.matrix@self.origin_a-self.node_a.matrix@self.point_a
        vb=self.node_b.matrix@self.origin_b-self.node_b.matrix@self.point_b

        fallback=0
        angle=va.angle(vb,fallback)
        axis=va.cross(vb)

        angle_shift=(target_angle-angle)/2

        parent_matrix=mathutils.Matrix.Identity(4)
        parent_matrix.col[3][0:3]=self.node_a.matrix@self.point_a

        rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(-angle_shift,4,axis)
        matrix_a[:]=rotation_matrix@parent_matrix.inverted()@matrix_a

        parent_matrix=mathutils.Matrix.Identity(4)
        parent_matrix.col[3][0:3]=self.node_b.matrix@self.point_b
        rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(angle_shift,4,axis)
        matrix_b[:]=rotation_matrix@parent_matrix.inverted()@matrix_b



    def is_valid(self):

        if self.node_a is not None and self.node_b is not None:
            return True
        else:
            return False


class TwinLink:
    def __init__(self,links):
        link=next(iter(links))
        self.node_a=link.node_a
        self.node_b=link.node_b
        self.links=links

        self.node=self.node_a
        self.other_node=self.node_b

    def __str__(self):
        return f"TWIN {self.node_a.source.name} {self.node_b.source.name} | "+" , ".join(
            [link.__str__() for link in self.links])

    def __repr__(self):
        return self.__str__()

    def set_active(self,node):
        if node is self.node_a:
            self.node=self.node_a
            self.other_node=self.node_b
        else:
            self.node=self.node_b
            self.other_node=self.node_a

    def snap(self,target=None):
        pass


def matrix_diff(matrix_a,matrix_b):
    out=0.0
    for x in range(4):
        for y in range(4):
            out+=matrix_a[x][y]-matrix_b[x][y]
    return out


# def compose_matrix(transform):
#     l,r,s=transform
#
#     if type(r)==mathutils.Quaternion:
#         rotation_matrix=mathutils.Matrix.Rotation(r.angle, 4, r.axis)
#     elif type(r)==tuple:
#         rotation_matrix=mathutils.Matrix.Rotation(r[3],4,(r[0],r[1],r[2]))
#     else:
#         rotation_matrix=r.to_matrix().to_4x4()
#
#     matrix=mathutils.Matrix.Translation(l)
#     matrix[0][0],matrix[1][1],matrix[2][2]=s
#
#
#
#     return matrix@rotation_matrix

def to_quaternion(rotation):
    if type(rotation)==mathutils.Quaternion:
        return rotation
    if type(rotation)==mathutils.Euler:
        return rotation.to_quaternion()
    if type(rotation)==mathutils.Vector:
        return mathutils.Quaternion(rotation[1:4],rotation[0])


def compose_matrix(transform):
    l,r,s=transform

    if type(r)==mathutils.Quaternion:
        rotation_matrix=mathutils.Matrix.Rotation(r.angle,4,r.axis)
    elif type(r)==tuple:
        rotation_matrix=mathutils.Matrix.Rotation(r[3],4,(r[0],r[1],r[2]))
    else:
        rotation_matrix=r.to_matrix().to_4x4()

    matrix=mathutils.Matrix.Identity(3)
    matrix[0][0],matrix[1][1],matrix[2][2]=s

    matrix.rotate(r)

    matrix=matrix.to_4x4()
    matrix.col[3]=l[0],l[1],l[2],1

    return matrix


def get_trajectories(bake_items,custom_range=None):
    pass  #print("GET TRAJECTORIES")
    last_frame=bpy.context.scene.frame_current

    min_frame=max_frame=0
    frame_ranges=[]
    for bake_item in bake_items:
        if type(bake_item)==bpy.types.PoseBone:
            action_holder=bake_item.id_data
        if type(bake_item)==bpy.types.Object:
            action_holder=bake_item
        frame_range=range(0,0)
        if action_holder.animation_data is not None:
            if action_holder.animation_data.action is not None:
                r=action_holder.animation_data.action.frame_range
                frame_range=range(math.floor(r[0]),math.ceil(r[1])+1)

                if custom_range is not None:
                    frame_range=range(max(frame_range.start,custom_range.start),
                                      min(frame_range.stop,custom_range.stop+1))

        frame_ranges.append(frame_range)

        min_frame=min(min_frame,frame_range.start)
        max_frame=max(max_frame,frame_range.stop)

    max_frame_range=range(min_frame,max_frame)

    # trajectories=[[] for item in bake_items]
    trajectories={}
    for item in bake_items:
        trajectories[item]=[]
    for f in max_frame_range:

        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()

        for item,frame_range in zip(bake_items,frame_ranges):
            if f in frame_range:
                if type(item)==bpy.types.PoseBone:
                    # m=item.id_data.convert_space(pose_bone=item,matrix=item.matrix,from_space='POSE',to_space='WORLD')
                    m=item.id_data.matrix_world@item.matrix
                    trajectories[item].append((m,f))
                if type(item)==bpy.types.Object:
                    trajectories[item].append((item.matrix_world.copy(),f))

    bpy.context.scene.frame_set(last_frame)
    return trajectories


def apply_trajectories(bake_items,trajectories,parents=None,apply_local=False,key_local=False):
    pass  #print("APPLY TRAJECTORIES")
    options={'INSERTKEY_NEEDED'}
    # options=set()
    # options = {'INSERTKEY_VISUAL'}

    # print(trajectories.keys())
    # for key in trajectories.keys():
    #     print(key.name,id(key))
    # print("AAA")
    for x in range(len(bake_items)):

        item=bake_items[x]
        parent=None
        parent_trajectory=None
        if parents is not None:
            parent=parents[x]
            if parent is not None:
                if parent in trajectories:
                    parent_trajectory=trajectories[parent]
                else:
                    parent=None

                # print(parent.name,id(parent))
                # parent_trajectory=trajectories[parent]
        trajectory=trajectories[item]

        euler_prev=None
        local_euler_prev=None
        for y in range(len(trajectory)):
            matrix,f=trajectory[y]
            if parent is not None:
                parent_matrix,parent_f=parent_trajectory[y]

            if type(item)==bpy.types.PoseBone:
                if parent is not None and apply_local:
                    item.matrix_basis=(parent_matrix@(parent.bone.matrix_local.inverted()@item.bone.matrix_local)).inverted()@matrix

                else:
                    item.matrix_basis=(item.id_data.matrix_basis@item.bone.matrix_local).inverted()@matrix
                # item.matrix_basis=(item.id_data.matrix_basis@item.bone.matrix_local).inverted()@matrix

            if type(item)==bpy.types.Object:
                item.matrix_basis=matrix.copy()

            item.keyframe_insert("location",index=-1,frame=f,group=item.name,options=options)

            rotation_mode=item.rotation_mode
            if rotation_mode=='QUATERNION':
                item.keyframe_insert("rotation_quaternion",index=-1,frame=f,group=item.name,options=options)
            elif rotation_mode=='AXIS_ANGLE':
                item.keyframe_insert("rotation_axis_angle",index=-1,frame=f,group=item.name,options=options)
            else:  # euler, XYZ, ZXY etc
                if euler_prev is not None:
                    euler=item.rotation_euler.copy()
                    euler.make_compatible(euler_prev)
                    item.rotation_euler=euler
                    euler_prev=euler
                    del euler
                else:
                    euler_prev=item.rotation_euler.copy()
                item.keyframe_insert("rotation_euler",index=-1,frame=f,group=item.name,options=options)

            if key_local and parent is not None:
                local_quaternion=parent_matrix.to_quaternion().inverted()@matrix.to_quaternion()
                if rotation_mode=='QUATERNION':
                    item.free_ik_local_quaternion=local_quaternion
                    item.keyframe_insert("free_ik_local_quaternion",index=-1,frame=f,group=item.name,options=options)
                elif rotation_mode=='AXIS_ANGLE':
                    axis=local_quaternion.axis
                    item.free_ik_local_axis_angle=local_quaternion.angle,axis[0],axis[1],axis[2]
                    item.keyframe_insert("free_ik_local_axis_angle",index=-1,frame=f,group=item.name,options=options)
                else:  # euler, XYZ, ZXY etc
                    local_euler=mathutils.Euler((0,0,0),rotation_mode)

                    local_euler.rotate(local_quaternion)
                    # local_euler=local_quaternion.to_euler()
                    if local_euler_prev is not None:
                        local_euler.make_compatible(local_euler_prev)
                    local_euler_prev=local_euler.copy()

                    item.free_ik_local_euler=local_euler
                    item.keyframe_insert("free_ik_local_euler",index=-1,frame=f,group=item.name,options=options)

            item.keyframe_insert("scale",index=-1,frame=f,group=item.name,options=options)


def make_new_action(items):
    for item in items:
        if item.animation_data is not None:
            if item.animation_data.action is not None:
                item.animation_data.action=bpy.data.actions.new(item.animation_data.action.name+"_baked")
                # name=item.animation_data.action.name+"_baked"
                # item.animation_data.action=item.animation_data.action.copy()
                # item.animation_data.action.name=name


def change_keyframes(some_object,delete_untagged=False,tag=False):
    if type(some_object)==bpy.types.PoseBone:
        base_path='pose.bones["{}"].'.format(some_object.name)
        fcurve_holder=some_object.id_data
    else:
        base_path=""
        fcurve_holder=some_object

    if some_object.rotation_mode=='QUATERNION':
        rotation_data_path=base_path+"rotation_quaternion"
    elif some_object.rotation_mode=='AXIS_ANGLE':
        rotation_data_path=base_path+"rotation_axis_angle"
    else:
        rotation_data_path=base_path+"rotation_euler"

    data_paths=(base_path+"location",rotation_data_path,base_path+"scale")

    if fcurve_holder.animation_data is not None:
        if fcurve_holder.animation_data.action is not None:
            fcurve_to_delete=None
            for fcurve in fcurve_holder.animation_data.action.fcurves:
                if fcurve.data_path in data_paths:

                    if delete_untagged:
                        keyframe_to_delete=None
                        for keyframe in fcurve.keyframe_points:
                            if keyframe.type!='EXTREME':
                                keyframe_to_delete=keyframe
                                break
                        while keyframe_to_delete is not None:
                            pass  #print(keyframe_to_delete.co,keyframe_to_delete.type)
                            fcurve.keyframe_points.remove(keyframe_to_delete,fast=False)
                            keyframe_to_delete=None
                            for keyframe in fcurve.keyframe_points:
                                if keyframe.type!='EXTREME':
                                    keyframe_to_delete=keyframe
                                    break
                        if len(fcurve.keyframe_points)==0:
                            fcurve_to_delete=fcurve

                    if tag:
                        for keyframe in fcurve.keyframe_points:
                            keyframe.type='EXTREME'

            while fcurve_to_delete is not None:
                fcurve_holder.animation_data.action.fcurves.remove(fcurve_to_delete)
                fcurve_to_delete=None
                for fcurve in fcurve_holder.animation_data.action.fcurves:
                    if len(fcurve.keyframe_points)==0:
                        fcurve_to_delete=fcurve
                        break


def get_raw_animated_transform(some_object,get_local=False):
    if type(some_object)==bpy.types.PoseBone:
        base_path='pose.bones["{}"].'.format(some_object.name)
        fcurve_holder=some_object.id_data
    else:
        base_path=""
        fcurve_holder=some_object

    location_curves=[None,None,None]
    location_data_path=base_path+"location"
    scale_curves=[None,None,None]
    scale_data_path=base_path+"scale"

    if some_object.rotation_mode=='QUATERNION':
        rotation_data_path=base_path+"rotation_quaternion"
        local_data_path=base_path+"free_ik_local_quaternion"
        rotation_curves=local_curves=[None,None,None,None]
    elif some_object.rotation_mode=='AXIS_ANGLE':
        rotation_data_path=base_path+"rotation_axis_angle"
        local_data_path=base_path+"free_ik_local_axis_angle"
        rotation_curves=local_curves=[None,None,None,None]
    else:
        rotation_data_path=base_path+"rotation_euler"
        local_data_path=base_path+"free_ik_local_euler"
        rotation_curves=local_curves=[None,None,None]

    if fcurve_holder.animation_data is not None:
        if fcurve_holder.animation_data.action is not None:

            location_curves=[fcurve_holder.animation_data.action.fcurves.find(location_data_path,index=x) for x in
                             range(len(location_curves))]
            rotation_curves=[fcurve_holder.animation_data.action.fcurves.find(rotation_data_path,index=x) for x in
                             range(len(rotation_curves))]
            scale_curves=[fcurve_holder.animation_data.action.fcurves.find(scale_data_path,index=x) for x in
                          range(len(scale_curves))]
            if get_local:
                local_curves=[fcurve_holder.animation_data.action.fcurves.find(local_data_path,index=x) for x in
                              range(len(local_curves))]

            frame=bpy.context.scene.frame_current

            location=[None if fcurve is None else fcurve.evaluate(frame) for fcurve in location_curves]
            scale=[None if fcurve is None else fcurve.evaluate(frame) for fcurve in scale_curves]
            rotation=[None if fcurve is None else fcurve.evaluate(frame) for fcurve in rotation_curves]

            # location=[None  for fcurve in location_curves]
            # scale=[None  for fcurve in scale_curves]
            # rotation=[None for fcurve in rotation_curves]

            if get_local:
                local_rotation=[None if fcurve is None else fcurve.evaluate(frame) for fcurve in local_curves]

                # local_rotation=[None for fcurve in local_curves]
                return location,rotation,scale,local_rotation,some_object.rotation_mode
            else:
                return location,rotation,scale,some_object.rotation_mode

    if get_local:
        return location_curves,rotation_curves,scale_curves,local_curves,some_object.rotation_mode
    else:
        return location_curves,rotation_curves,scale_curves,some_object.rotation_mode


#
# def get_raw_animated_transform(some_object):
#
#     if type(some_object)==bpy.types.PoseBone:
#         base_path='pose.bones["{}"].'.format(some_object.name)
#         fcurve_holder=some_object.id_data
#     else:
#         base_path=""
#         fcurve_holder=some_object
#
#     # pass#print(type(some_object))
#
#
#     if fcurve_holder.animation_data is not None:
#         if fcurve_holder.animation_data.action is not None:
#             location_curves=[None,None,None]
#             location_data_path=base_path+"location"
#             scale_curves=[None,None,None]
#             scale_data_path=base_path+"scale"
#
#             if some_object.rotation_mode=='QUATERNION':
#                 rotation_data_path=base_path+"rotation_quaternion"
#                 rotation_curves=[None,None,None,None]
#                 curve_count=10
#             elif some_object.rotation_mode=='AXIS_ANGLE':
#                 rotation_data_path=base_path+"rotation_axis_angle"
#                 rotation_curves=[None,None,None,None]
#                 curve_count=10
#             else:
#                 rotation_data_path=base_path+"rotation_euler"
#                 rotation_curves=[None,None,None]
#                 curve_count=9
#
#             # pass#print(rotation_data_path)
#
#             curve_counter=0
#
#             for fcurve in fcurve_holder.animation_data.action.fcurves:
#                 # pass#print(fcurve.data_path)
#                 # pass#print(rotation_data_path)
#                 # pass#print(fcurve.data_path==rotation_data_path)
#                 if fcurve.data_path==location_data_path:
#                     location_curves[fcurve.array_index]=fcurve
#                     curve_counter+=1
#                 if fcurve.data_path==scale_data_path:
#                     scale_curves[fcurve.array_index]=fcurve
#                     curve_counter+=1
#                 if fcurve.data_path==rotation_data_path:
#                     rotation_curves[fcurve.array_index]=fcurve
#                     curve_counter+=1
#                 if curve_counter==curve_count:
#                     break
#
#             frame=bpy.context.scene.frame_current
#
#
#
#             location=tuple(None if fcurve is None else fcurve.evaluate(frame) for fcurve in location_curves)
#             scale=tuple(None if fcurve is None else fcurve.evaluate(frame) for fcurve in scale_curves)
#             rotation=tuple(None if fcurve is None else fcurve.evaluate(frame) for fcurve in rotation_curves)
#
#
#             return  location,rotation,scale,some_object.rotation_mode
#
#     return None


def get_transform_tuple(some_object):
    if some_object.rotation_mode=='QUATERNION':
        rotation=some_object.rotation_quaternion.copy()
    elif some_object.rotation_mode=='AXIS_ANGLE':
        rotation=mathutils.Vector(some_object.rotation_axis_angle)
    else:
        rotation=some_object.rotation_euler.copy()

    return some_object.location.copy(),rotation,some_object.scale.copy()


def apply_transform_tuple(some_object,transform_tuple):
    l,r,s=transform_tuple
    some_object.location=l
    some_object.scale=s
    if type(r)==mathutils.Quaternion:
        some_object.rotation_quaternion=r
    if type(r)==mathutils.Euler:
        some_object.rotation_euler=r
    if type(r)==mathutils.Vector:
        some_object.rotation_axis_angle=r


def transform_from_raw(raw_transform,default_transform):
    if raw_transform is not None:
        location,rotation,scale,rotation_mode=raw_transform
    else:
        return default_transform

    default_location,default_rotation,default_scale=default_transform

    out_location=mathutils.Vector(
        default_value if value is None else value for default_value,value in zip(default_location,location))
    out_scale=mathutils.Vector(
        default_value if value is None else value for default_value,value in zip(default_scale,scale))

    if rotation_mode=='QUATERNION':
        out_rotation=mathutils.Quaternion(
            default_value if value is None else value for default_value,value in zip(default_rotation,rotation))
    elif rotation_mode=='AXIS_ANGLE':
        out_rotation=tuple(
            default_value if value is None else value for default_value,value in zip(default_rotation,rotation))
    else:
        out_rotation=mathutils.Euler(
            (default_value if value is None else value for default_value,value in zip(default_rotation,rotation)),
            rotation_mode)

    return out_location,out_rotation,out_scale


class RawTransform:
    def __init__(self,node):
        self.node=node
        self.is_bone=self.node.is_bone

        self.location=[None,None,None]
        self.rotation_quaternion=[None,None,None,None]
        self.rotation_euler=[None,None,None]
        self.rotation_axis_angle=[None,None,None,None]
        self.scale=[None,None,None]

        self.local_quaternion=[None,None,None,None]
        self.local_euler=[None,None,None]
        self.local_axis_angle=[None,None,None,None]

        self.rotation_mode='QUATERNION'
        self.rotation=self.rotation_quaternion
        self.local_rotation=self.local_quaternion

        if self.node.is_bone:
            self.armature_location=[None,None,None]
            self.armature_rotation_quaternion=[None,None,None,None]
            self.armature_rotation_euler=[None,None,None]
            self.armature_rotation_axis_angle=[None,None,None,None]
            self.armature_scale=[None,None,None]
            self.armature_rotation_mode='QUATERNION'
            self.armature_rotation=self.armature_rotation_quaternion
        self.is_consistent=True
        self.from_node()

    def from_node(self):

        self.location,self.rotation,self.scale,self.local_rotation,self.rotation_mode=get_raw_animated_transform(
            self.node.source,get_local=True)
        if self.rotation_mode=='QUATERNION':
            self.rotation_quaternion=self.rotation
            self.local_quaternion=self.local_rotation
        elif self.rotation_mode=='AXIS_ANGLE':
            self.rotation_axis_angle=self.rotation
            self.local_axis_angle=self.local_rotation
        else:
            self.rotation_euler=self.rotation
            self.local_euler=self.local_rotation

        if self.is_bone:
            self.armature_location,self.armature_rotation,self.armature_scale,self.armature_rotation_mode=get_raw_animated_transform(
                self.node.source_armature)
            if self.armature_rotation_mode=='QUATERNION':
                self.armature_rotation_quaternion=self.rotation
            elif self.armature_rotation_mode=='AXIS_ANGLE':
                self.armature_rotation_axis_angle=self.rotation
            else:
                self.armature_rotation_euler=self.rotation

        # pass#print(self.location,self.rotation,self.scale,self.local_rotation,self.rotation_mode)

        self.is_consistent=(not any(self.location) or all(self.location)) and (
                    not any(self.rotation) or all(self.rotation)) and (not any(self.scale) or all(self.scale))

    def update_active_rotation(self):
        self.rotation_mode=self.node.source.rotation_mode
        if self.rotation_mode=='QUATERNION':
            self.rotation=self.rotation_quaternion
            self.local_rotation=self.local_quaternion
        elif self.rotation_mode=='AXIS_ANGLE':
            self.rotation=self.rotation_axis_angle
            self.local_rotation=self.local_axis_angle
        else:
            self.rotation=self.rotation_euler
            self.local_rotation=self.local_euler

    def from_other(self,other):

        self.location=other.location
        self.rotation_quaternion=other.rotation_quaternion
        self.rotation_euler=other.rotation_euler
        self.rotation_axis_angle=other.rotation_axis_angle
        self.scale=other.scale

        self.local_quaternion=other.local_quaternion
        self.local_euler=other.local_euler
        self.local_axis_angle=other.local_axis_angle

        self.rotation_mode=other.rotation_mode
        self.rotation=other.rotation
        self.local_rotation=other.local_rotation

        if self.node.is_bone:
            self.armature_location=other.armature_location
            self.armature_rotation_quaternion=other.armature_rotation_quaternion
            self.armature_rotation_euler=other.armature_rotation_euler
            self.armature_rotation_axis_angle=other.armature_rotation_axis_angle
            self.armature_scale=other.armature_scale
            self.armature_rotation_mode=other.armature_rotation_mode
            self.armature_rotation=other.armature_rotation
        self.is_consistent=other.is_consistent

    def get_reference_rotation(self,default):
        out=default.rotation.copy()
        for x in range(len(out)):
            if self.rotation[x] is not None:
                out[x]=self.rotation[x]
        return out

    def get_reference_local_rotation(self,default):
        out=default.local_rotation.copy()
        for x in range(len(out)):
            if self.local_rotation[x] is not None:
                out[x]=self.local_rotation[x]
        return out

    def get_reference_scale(self,default):
        out=default.scale.copy()
        for x in range(len(out)):
            if self.scale[x] is not None:
                out[x]=self.scale[x]
        return out

    def get_matrix(self,default):

        temp_transforms=(default.location.copy(),default.rotation.copy(),default.scale.copy(),default.local_rotation)
        raw_transforms=(self.location,self.rotation,self.scale,self.local_rotation)

        for temp_transform,raw_transform in zip(temp_transforms,raw_transforms):
            for x in range(len(raw_transform)):
                if raw_transform[x] is not None:
                    temp_transform[x]=raw_transform[x]

        local_quaternion=to_quaternion(temp_transforms[3])
        out_transform=temp_transforms[:3]

        if self.is_bone:
            out_matrix=self.node.armature_matrix_basis@self.node.matrix_local@compose_matrix(out_transform)
        else:
            out_matrix=compose_matrix(out_transform)

        if self.node.frame_parent is not None and not self.node.is_pinned:
            location,rotation,scale=out_matrix.decompose()
            rotation=self.node.frame_parent.matrix.to_quaternion()@local_quaternion
            out_matrix=compose_matrix((location,rotation,scale))

        return out_matrix

    def simple_compare(self,other):
        if self.is_bone:
            return self.location==other.location and self.rotation==other.rotation and self.scale==other.scale and self.local_rotation==other.local_rotation and self.armature_location==other.armature_location and self.armature_rotation==other.armature_rotation and self.armature_scale==other.armature_scale
        else:
            return self.location==other.location and self.rotation==other.rotation and self.scale==other.scale and self.local_rotation==other.local_rotation


class FullTransform:
    def __init__(self,node):
        self.node=node
        self.is_bone=self.node.is_bone
        self.location=mathutils.Vector((0,0,0))
        self.rotation_quaternion=mathutils.Quaternion()
        self.rotation_euler=mathutils.Euler()
        self.rotation_axis_angle=mathutils.Vector((0,0,0,0))
        self.scale=mathutils.Vector((0,0,0))
        self.rotation_mode='QUATERNION'
        self.rotation=None
        self.local_rotation=None

        self.local_quaternion=mathutils.Quaternion()
        self.local_euler=mathutils.Euler()
        self.local_axis_angle=mathutils.Vector((0,0,0,0))

        self.limit_rotation=mathutils.Euler()

        if self.node.is_bone:
            self.armature_location=mathutils.Vector((0,0,0))
            self.armature_rotation_quaternion=mathutils.Quaternion()
            self.armature_rotation_euler=mathutils.Euler()
            self.armature_rotation_axis_angle=mathutils.Vector((0,0,0,0))
            self.armature_scale=mathutils.Vector((0,0,0))
            self.armature_rotation_mode='QUATERNION'
            self.armature_rotation=None
        self.from_node()

        self.source_location=self.node.source.location
        self.source_rotation_quaternion=self.node.source.rotation_quaternion
        self.source_rotation_euler=self.node.source.rotation_euler
        self.source_rotation_axis_angle=self.node.source.rotation_axis_angle
        self.source_scale=self.node.source.scale

    def update_armature_transform(self):
        if self.node.is_bone:
            self.armature_location[:]=self.node.source_armature.location
            self.armature_rotation_quaternion[:]=self.node.source_armature.rotation_quaternion
            self.armature_rotation_euler[:]=self.node.source_armature.rotation_euler
            self.armature_rotation_euler.order=self.node.source_armature.rotation_euler.order
            self.armature_rotation_axis_angle[:]=self.node.source_armature.rotation_axis_angle
            self.armature_scale[:]=self.node.source_armature.scale
            self.armature_rotation_mode=self.node.source_armature.rotation_mode
            if self.armature_rotation_mode=='QUATERNION':
                self.armature_rotation=self.armature_rotation_quaternion
            elif self.armature_rotation_mode=='AXIS_ANGLE':
                self.armature_rotation=self.armature_rotation_axis_angle
            else:
                self.armature_rotation=self.armature_rotation_euler

    def merge(self,other,mask: RawTransform):
        own_transforms=(self.location,self.rotation,self.scale)
        other_transforms=(other.location,other.rotation,other.scale)
        mask_transforms=(mask.location,mask.rotation,mask.scale)

        for own_transform,other_transform,mask_transform in zip(own_transforms,other_transforms,mask_transforms):
            for x in range(len(own_transform)):
                if mask_transform[x] is None:
                    own_transform[x]=other_transform[x]

    def merge_with_raw(self,other: RawTransform):
        own_transforms=(self.location,self.rotation,self.scale)
        other_transforms=(other.location,other.rotation,other.scale)

        for own_transform,other_transform in zip(own_transforms,other_transforms):
            for x in range(len(own_transform)):
                if other_transform[x] is not None:
                    own_transform[x]=other_transform[x]

    def update_active_rotation(self):
        self.rotation_mode=self.node.source.rotation_mode
        if self.rotation_mode=='QUATERNION':
            self.rotation=self.rotation_quaternion
            self.local_rotation=self.local_quaternion
        elif self.rotation_mode=='AXIS_ANGLE':
            self.rotation=self.rotation_axis_angle
            self.local_rotation=self.local_axis_angle
        else:
            self.rotation=self.rotation_euler
            self.local_rotation=self.local_euler

    def from_node(self):

        self.location[:]=self.node.source.location
        self.rotation_quaternion[:]=self.node.source.rotation_quaternion
        self.rotation_euler[:]=self.node.source.rotation_euler
        self.rotation_euler.order=self.node.source.rotation_euler.order
        self.rotation_axis_angle[:]=self.node.source.rotation_axis_angle
        self.scale[:]=self.node.source.scale
        self.rotation_mode=self.node.source.rotation_mode

        self.local_quaternion[:]=self.node.source.free_ik_local_quaternion
        self.local_euler[:]=self.node.source.free_ik_local_euler
        self.local_euler.order=self.node.source.free_ik_local_euler.order
        self.local_axis_angle[:]=self.node.source.free_ik_local_axis_angle

        if self.rotation_mode=='QUATERNION':
            self.rotation=self.rotation_quaternion
            self.local_rotation=self.local_quaternion
        elif self.rotation_mode=='AXIS_ANGLE':
            self.rotation=self.rotation_axis_angle
            self.local_rotation=self.local_axis_angle
        else:
            self.rotation=self.rotation_euler
            self.local_rotation=self.local_euler

        if False:
            self.limit_rotation[:]=self.node.source.matrix_basis.to_euler()
            # self.limit_rotation.order=self.rotation_euler.order

        if True:
            r=self.node.source.matrix_basis.to_quaternion()
            e=mathutils.Euler()
            e.order=self.rotation_euler.order

            e.rotate(r)

            self.limit_rotation[:] = e

        self.update_armature_transform()


    def from_other_source(self,source):

        self.location[:]=source.location
        self.rotation_quaternion[:]=source.rotation_quaternion
        self.rotation_euler[:]=source.rotation_euler
        self.rotation_euler.order=source.rotation_euler.order
        self.rotation_axis_angle[:]=source.rotation_axis_angle
        self.scale[:]=source.scale
        self.rotation_mode=source.rotation_mode

        self.local_quaternion[:]=source.free_ik_local_quaternion
        self.local_euler[:]=source.free_ik_local_euler
        self.local_euler.order=source.free_ik_local_euler.order
        self.local_axis_angle[:]=source.free_ik_local_axis_angle

        if self.rotation_mode=='QUATERNION':
            self.rotation=self.rotation_quaternion
            self.local_rotation=self.local_quaternion
        elif self.rotation_mode=='AXIS_ANGLE':
            self.rotation=self.rotation_axis_angle
            self.local_rotation=self.local_axis_angle
        else:
            self.rotation=self.rotation_euler
            self.local_rotation=self.local_euler


        self.limit_rotation[:]=source.matrix_basis.to_euler()
        # self.limit_rotation.order=self.rotation_euler.order

        if self.node.is_bone:
            source_armature=source.id_data
            self.armature_location[:]=source_armature.location
            self.armature_rotation_quaternion[:]=source_armature.rotation_quaternion
            self.armature_rotation_euler[:]=source_armature.rotation_euler
            self.armature_rotation_euler.order=source_armature.rotation_euler.order
            self.armature_rotation_axis_angle[:]=source_armature.rotation_axis_angle
            self.armature_scale[:]=source_armature.scale
            self.armature_rotation_mode=source_armature.rotation_mode
            if self.armature_rotation_mode=='QUATERNION':
                self.armature_rotation=self.armature_rotation_quaternion
            elif self.armature_rotation_mode=='AXIS_ANGLE':
                self.armature_rotation=self.armature_rotation_axis_angle
            else:
                self.armature_rotation=self.armature_rotation_euler




    def make_compatible(self,q,e,a,reference):
        if type(reference)==mathutils.Quaternion:
            if reference.dot(-q)>reference.dot(q): q.negate()
        elif type(reference)==mathutils.Vector:
            if reference.dot(-a)>reference.dot(a): a[:]=-a
        elif type(reference)==mathutils.Euler:

            e.make_compatible(reference)

    def from_matrix(self,matrix):

        if self.is_bone:
            work_matrix=(self.node.armature_matrix_basis@self.node.matrix_local).inverted()@matrix

        else:
            work_matrix=matrix



        self.location[:],self.rotation_quaternion[:],self.scale[:]=work_matrix.decompose()

        if self.node.reference_scale is not None:
            self.scale[:]=mathutils.Vector(
                math.copysign(reference,out) for reference,out in zip(self.node.reference_scale,self.scale))

        if type(self.node.reference_rotation)==mathutils.Euler:
            self.rotation_euler.zero()
            self.rotation_euler.order=self.node.reference_rotation.order
            self.rotation_euler.rotate(self.rotation_quaternion)
        else:
            self.rotation_euler[:]=self.rotation_quaternion.to_euler()

        axis=self.rotation_quaternion.axis
        self.rotation_axis_angle[:]=mathutils.Vector((self.rotation_quaternion.angle,axis[0],axis[1],axis[2]))


        if self.node.reference_rotation is not None:
            self.make_compatible(self.rotation_quaternion,self.rotation_euler,self.rotation_axis_angle,self.node.reference_rotation)


        if self.node.frame_parent is not None:
            self.local_quaternion[:]=self.node.frame_parent.matrix.to_quaternion().inverted()@self.node.matrix.to_quaternion()
        else:
            self.local_quaternion.identity()


        if type(self.node.reference_rotation)==mathutils.Euler:
            self.local_euler.zero()
            self.local_euler.order=self.node.reference_rotation.order
            self.local_euler.rotate(self.local_quaternion)
        else:
            self.local_euler[:]=self.local_quaternion.to_euler()

        axis=self.local_quaternion.axis
        self.local_axis_angle[:]=mathutils.Vector((self.local_quaternion.angle,axis[0],axis[1],axis[2]))

        if self.node.reference_local_rotation is not None:
            self.make_compatible(self.local_quaternion,self.local_euler,self.local_axis_angle,self.node.reference_local_rotation)


        # self.limit_rotation[:]=self.rotation_quaternion.to_euler()

        self.limit_rotation.zero()
        self.limit_rotation.order=self.rotation_euler.order
        self.limit_rotation.rotate(self.rotation_quaternion)


        # self.limit_rotation[:]=self.rotation_euler
        # self.limit_rotation.order=self.rotation_euler.order

        self.update_armature_transform()

    def from_other(self,other):
        self.location[:]=other.location
        self.rotation_quaternion[:]=other.rotation_quaternion
        self.rotation_euler[:]=other.rotation_euler
        self.rotation_euler.order=other.rotation_euler.order
        self.rotation_axis_angle[:]=other.rotation_axis_angle
        self.scale[:]=other.scale
        self.rotation_mode=other.rotation_mode

        self.local_quaternion[:]=other.local_quaternion
        self.local_euler[:]=other.local_euler
        self.local_euler.order=other.local_euler.order
        self.local_axis_angle[:]=other.local_axis_angle

        if self.rotation_mode=='QUATERNION':
            self.rotation=self.rotation_quaternion
            self.local_rotation=self.local_quaternion
        elif self.rotation_mode=='AXIS_ANGLE':
            self.rotation=self.rotation_axis_angle
            self.local_rotation=self.local_axis_angle
        else:
            self.rotation=self.rotation_euler
            self.local_rotation=self.local_euler

        self.limit_rotation[:]=other.limit_rotation
        self.limit_rotation.order=other.limit_rotation.order

        if self.node.is_bone:
            self.armature_location[:]=other.armature_location
            self.armature_rotation_quaternion[:]=other.armature_rotation_quaternion
            self.armature_rotation_euler[:]=other.armature_rotation_euler
            self.armature_rotation_euler.order=other.armature_rotation_euler.order
            self.armature_rotation_axis_angle[:]=other.armature_rotation_axis_angle
            self.armature_scale[:]=other.armature_scale
            self.armature_rotation_mode=other.armature_rotation_mode
            if self.armature_rotation_mode=='QUATERNION':
                self.armature_rotation=self.armature_rotation_quaternion
            elif self.armature_rotation_mode=='AXIS_ANGLE':
                self.armature_rotation=self.armature_rotation_axis_angle
            else:
                self.armature_rotation=self.armature_rotation_euler

        pass

    def from_raw(self):
        pass

    def compare(self,other):

        is_translating=(self.location!=other.location)
        is_rotating=(self.rotation!=other.rotation)
        is_scaling=(self.scale!=other.scale)
        is_armature_shift=False

        # if is_rotating:
        #     print(tuple(self.rotation))
        #     print(tuple(other.rotation))

        if self.is_bone:
            is_armature_translating=self.armature_location!=other.armature_location
            is_armature_rotating=self.armature_rotation!=other.armature_rotation
            is_armature_scaling=self.armature_scale!=other.armature_scale

            is_translating=is_translating or is_armature_translating
            is_rotating=is_rotating or is_armature_rotating
            is_scaling=is_scaling or is_armature_scaling

            is_armature_shift=is_armature_translating or is_armature_rotating or is_armature_scaling

        return is_translating,is_rotating,is_scaling,is_armature_shift

    def simple_compare(self,other):
        if self.is_bone:
            return self.location==other.location and self.rotation==other.rotation and self.scale==other.scale and self.local_rotation==other.local_rotation and self.armature_location==other.armature_location and self.armature_rotation==other.armature_rotation and self.armature_scale==other.armature_scale
        else:
            return self.location==other.location and self.rotation==other.rotation and self.scale==other.scale and self.local_rotation==other.local_rotation

    def compare_with_source(self):

        if self.node.source.rotation_mode=='QUATERNION':
            source_rotation=self.node.rotation_quaternion
        elif self.node.source.rotation_mode=='AXIS_ANGLE':
            source_rotation=mathutils.Vector(self.node.rotation_axis_angle)
        else:
            source_rotation=self.node.rotation_euler

        is_translating=self.location!=self.node.location
        is_rotating=self.rotation!=source_rotation
        is_scaling=self.scale!=self.node.scale
        is_armature_shift=False

        if self.is_bone:

            if self.node.source_armature.rotation_mode=='QUATERNION':
                source_armature_rotation=self.node.armature_rotation_quaternion
            elif self.node.source_armature.rotation_mode=='AXIS_ANGLE':
                source_armature_rotation=mathutils.Vector(self.node.armature_rotation_axis_angle)
            else:
                source_armature_rotation=self.node.armature_rotation_euler

            is_armature_translating=self.armature_location!=self.node.armature_location
            is_armature_rotating=self.armature_rotation!=source_armature_rotation
            is_armature_scaling=self.armature_scale!=self.node.armature_scale

            is_translating=is_translating or is_armature_translating
            is_rotating=is_rotating or is_armature_rotating
            is_scaling=is_scaling or is_armature_scaling

            is_armature_shift=is_armature_translating or is_armature_rotating or is_armature_scaling

        return is_translating,is_rotating,is_scaling,is_armature_shift

    def simple_compare_with_source(self):

        if self.node.source.rotation_mode=='QUATERNION':
            source_rotation=self.node.rotation_quaternion
        elif self.node.source.rotation_mode=='AXIS_ANGLE':
            source_rotation=mathutils.Vector(self.node.rotation_axis_angle)
        else:
            source_rotation=self.node.rotation_euler

        if self.is_bone:
            if self.node.source_armature.rotation_mode=='QUATERNION':
                source_armature_rotation=self.node.armature_rotation_quaternion
            elif self.node.source_armature.rotation_mode=='AXIS_ANGLE':
                source_armature_rotation=mathutils.Vector(self.node.armature_rotation_axis_angle)
            else:
                source_armature_rotation=self.node.armature_rotation_euler

            return self.location==self.node.location and self.rotation==source_rotation and self.scale==self.node.scale and self.armature_location==self.node.armature_location and self.armature_rotation==source_armature_rotation and self.armature_scale==self.node.armature_scale
        else:
            return self.location==self.node.location and self.rotation==source_rotation and self.scale==self.node.scale

    def apply_to_limit(self):
        self.node.source.free_ik.limit_location=self.location
        self.node.source.free_ik.limit_rotation=self.limit_rotation
        self.node.source.free_ik.limit_scale=self.scale

    # def apply_to_limit(self):
    #
    #     self.limit_location.min_x=self.location.x
    #     self.limit_location.min_y=self.location.y
    #     self.limit_location.min_z=self.location.z
    #
    #     self.limit_location.max_x=self.location.x
    #     self.limit_location.max_y=self.location.y
    #     self.limit_location.max_z=self.location.z
    #
    #     #
    #     self.limit_rotation.min_x=self.rotation_euler.x
    #     self.limit_rotation.min_y=self.rotation_euler.y
    #     self.limit_rotation.min_z=self.rotation_euler.z
    #
    #     self.limit_rotation.max_x=self.rotation_euler.x
    #     self.limit_rotation.max_y=self.rotation_euler.y
    #     self.limit_rotation.max_z=self.rotation_euler.z
    #     #
    #     self.limit_scale.min_x=self.scale.x
    #     self.limit_scale.min_y=self.scale.y
    #     self.limit_scale.min_z=self.scale.z
    #
    #     self.limit_scale.max_x=self.scale.x
    #     self.limit_scale.max_y=self.scale.y
    #     self.limit_scale.max_z=self.scale.z

    # def apply_to_limit(self):
    #     if gv.limit_location_name in self.node.source.constraints:
    #
    #
    #         const=self.node.source.constraints[gv.limit_location_name]
    #         const.min_x=const.max_x=self.location.x
    #         const.min_y=const.max_y=self.location.y
    #         const.min_z=const.max_z=self.location.z
    #
    #     if gv.limit_rotation_name in self.node.source.constraints:
    #         const=self.node.source.constraints[gv.limit_rotation_name]
    #         const.min_x=const.max_x=self.rotation_euler.x
    #         const.min_y=const.max_y=self.rotation_euler.y
    #         const.min_z=const.max_z=self.rotation_euler.z
    #
    #     if gv.limit_scale_name in self.node.source.constraints:
    #         const=self.node.source.constraints[gv.limit_scale_name]
    #         const.min_x=const.max_x=self.scale.x
    #         const.min_y=const.max_y=self.scale.y
    #         const.min_z=const.max_z=self.scale.z
    def apply_to_base(self):
        pass

        self.node.source.location=self.location
        self.node.source.rotation_quaternion=self.rotation_quaternion
        self.node.source.rotation_euler=self.rotation_euler
        self.node.source.rotation_axis_angle=self.rotation_axis_angle
        self.node.source.scale=self.scale

        self.node.source.free_ik_local_quaternion=self.local_quaternion
        self.node.source.free_ik_local_euler=self.local_euler
        self.node.source.free_ik_local_axis_angle=self.local_axis_angle



class LineLink:
    def __init__(self,start_node,start_link,beam_nodes,beam_links,end_node,end_link):

        self.start_node=start_node  #type:Node
        self.start_link=start_link  #type:Link
        self.beam_nodes=beam_nodes  #type List[Node]
        self.beam_links=beam_links  #type List[Link]
        self.end_node=end_node  #type:Node
        self.end_link=end_link  #type:Link

        self.cluster=start_node.cluster

        self.length=0
        self.min_length=0
        self.max_length=0

        self.node_a=self.start_node
        self.node_b=self.end_node
        self.nodes=(self.node_a,self.node_b)

        self.start_link.set_active(self.start_node)
        self.end_link.set_active(self.end_node)

        self.point_a=self.start_link.point
        self.point_b=self.end_link.point

        self.origin_a=self.start_link.origin
        self.origin_b=self.end_link.origin

        self.error=self.get_error()

        self.solve_blanks=[]

        self.forward=[]
        self.backward=[]

        self.forward.append((self.start_link,self.start_node,self.beam_nodes[0]))
        for x in range(len(self.beam_links)):
            self.forward.append((self.beam_links[x],self.beam_nodes[x],self.beam_nodes[x+1]))

        self.backward.append((self.end_link,self.end_node,self.beam_nodes[len(self.beam_nodes)-1]))
        for x in range(len(self.beam_links)-1,-1,-1):
            self.backward.append((self.beam_links[x],self.beam_nodes[x+1],self.beam_nodes[x]))

        self.solve_blanks=self.forward+self.backward

        self.cummulative_angle=0

        work_nodes=set((self.start_node,*self.beam_nodes,self.end_node))

        work_links=self.start_link,*self.beam_links,self.end_link

        self.initial_origins=[[link.origin_a,link.origin_b] for link in work_links]
        self.work_origins=[link.get_origins(work_nodes) for link in work_links]

    def __str__(self):
        # return f"LINK {self.source.name}  {self.node_a.source.name}<->{self.node_b.source.name}"
        line_nodes=[self.start_node]
        line_nodes.extend(self.beam_nodes)
        line_nodes.append(self.end_node)

        line_links=[self.start_link]
        line_links.extend(self.beam_links)
        line_links.append(self.end_link)
        out="LINE "
        for x in range(len(line_nodes)):
            out+=f" {line_nodes[x].__str__()} "
            # if x in range(len(line_links)):
            #     out+=f" - {line_links[x].__str__()} - "

        return out

    def __repr__(self):
        return self.__str__()

    # def get_error(self):
    #     return max((link.get_error() for link in self.work_links))


    def set_initial_origins(self):
        work_links = self.start_link, *self.beam_links, self.end_link
        for link,origins in zip(work_links,self.initial_origins):
            link.origin_a,link.origin_b=origins

    def set_work_origins(self):
        work_links = self.start_link, *self.beam_links, self.end_link
        for link,origins in zip(work_links,self.work_origins):
            link.origin_a,link.origin_b=origins

    def get_error(self):
        current_length=(self.node_a.matrix@self.point_a-self.node_b.matrix@self.point_b).length
        # print(current_length)

        if self.length==0:
            return 0
        else:
            return max(max(0,self.min_length-current_length),max(0,current_length-self.max_length))/self.length



    def prepare(self):
        self.set_work_origins()


        work_links=[self.start_link]+self.beam_links+[self.end_link]
        beam_count=len(self.beam_nodes)

        self.max_length=0
        max_segment=None


        for x in range(beam_count):

            before_link=work_links[x]
            after_link=work_links[x+1]
            node=self.beam_nodes[x]

            before_link.set_active(self.beam_nodes[x])
            if x==beam_count-1:
                after_link.set_active(self.end_node)
            else:
                after_link.set_active(self.beam_nodes[x+1])

            segment=(node.matrix@before_link.point-node.matrix@after_link.other_point).length


            self.max_length+=segment

            if max_segment is None:
                max_segment=segment
            else:
                max_segment=max(segment,max_segment)



        self.min_length=max( 0,max_segment*2-self.max_length)


        self.length=((self.node_a.matrix@self.origin_a-self.node_a.matrix@self.point_a).length+(
                    self.node_b.matrix@self.origin_b-self.node_b.matrix@self.point_b).length)*0.5

        self.set_initial_origins()


    def track_to(self,target=None,only_translate=False):
        point_a_world=self.node_a.matrix@self.point_a
        point_b_world=self.node_b.matrix@self.point_b
        length=(point_a_world-point_b_world).length

        if length>self.max_length or length<self.min_length:
            direction_a=(point_b_world-point_a_world).normalized()
            direction_b=(point_a_world-point_b_world).normalized()

            if length>self.max_length:
                d=length-self.max_length
            if length<self.min_length:
                d=length-self.min_length


            if target is self.node_a :
                to_point(self.node_b.matrix,self.point_b,self.origin_b,point_b_world+direction_b*d,only_translate=self.node_b.is_only_translated or only_translate)

            elif target is self.node_b :
                to_point(self.node_a.matrix,self.point_a,self.origin_a,point_a_world+direction_a*d,only_translate=self.node_a.is_only_translated or only_translate)

            elif target is None:
                to_point(self.node_a.matrix,self.point_a,self.origin_a,point_a_world+direction_a*d*0.5,only_translate=self.node_a.is_only_translated or only_translate)
                to_point(self.node_b.matrix,self.point_b,self.origin_b,point_b_world+direction_b*d*0.5,only_translate=self.node_b.is_only_translated or only_translate)




    def smooth(self,parent,node):

        local_before=parent.initial_matrix.inverted()@node.initial_matrix
        local_after=parent.matrix.inverted()@node.matrix

        local_before.normalize()
        local_after.normalize()

        node.matrix[:]=parent.matrix@local_before.lerp(local_after,0.9)

        node.matrix.normalize()



    def rotate(self,origin,axis,angle,matrix):
        parent_matrix=mathutils.Matrix.Identity(4)
        parent_matrix.col[3][0:3]=origin
        parent_inverted=parent_matrix.inverted()

        rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(angle,4,axis)
        matrix[:]=rotation_matrix@parent_inverted@matrix


    def stretch(self):

        self.start_link.set_active(self.start_node)
        self.end_link.set_active(self.end_node)

        chain_vector=self.end_link.other_node.matrix@self.end_link.other_point-self.start_link.other_node.matrix@self.start_link.other_point
        chain_target_vector=self.end_link.node.matrix@self.end_link.point-self.start_link.node.matrix@self.start_link.point


        origin_point=self.start_link.node.matrix@self.start_link.point

        before_length=chain_vector.length
        after_length=chain_target_vector.length

        before_matrix=mathutils.Matrix.Identity(4)



        vx=chain_vector.normalized()
        vy=chain_vector.cross(chain_target_vector).normalized()
        vz=vx.cross(vy).normalized()
        vt=origin_point

        before_matrix.col[0][0:3]=vx*before_length
        before_matrix.col[1][0:3]=vy
        before_matrix.col[2][0:3]=vz
        before_matrix.col[3][0:3]=vt

        after_matrix=before_matrix.copy()
        after_matrix.col[0][0:3]=vx*after_length

        for node in self.beam_nodes:
            point_a,point_b=node.points
            center=(point_a+point_b)/2

            before_vector=node.matrix@point_b-node.matrix@point_a

            scaled_matrix=after_matrix@before_matrix.inverted_safe()@node.matrix
            after_vector=scaled_matrix@point_b-scaled_matrix@point_a

            origin=(node.matrix@point_a+node.matrix@point_b)/2
            # origin=node.matrix@point_a
            axis=before_vector.cross(after_vector)
            angle=before_vector.angle(after_vector,0)

            # print(axis.length)
            # if axis.length==0 and after_vector.length<before_vector.length:
            #     print("AAA")
            #     axis=mathutils.Vector((1,0,0))
            #     angle= math.acos(after_vector.length/before_vector.length)
            #



            self.rotate(origin,axis,angle,node.matrix)


            node.matrix.col[3][0:3]=node.matrix.to_translation()+scaled_matrix@center-node.matrix@center

    def align(self):
        self.start_link.set_active(self.start_node)
        self.end_link.set_active(self.end_node)

        chain_vector=self.end_link.other_node.matrix@self.end_link.other_point-self.start_link.other_node.matrix@self.start_link.other_point
        chain_target_vector=self.end_link.node.matrix@self.end_link.point-self.start_link.node.matrix@self.start_link.point

        origin=self.start_link.node.matrix@self.start_link.point

        axis=chain_vector.cross(chain_target_vector)
        angle=chain_vector.angle(chain_target_vector,0)

        for node in self.beam_nodes:
            self.rotate(origin,axis,angle,node.matrix)

    def align_optimal(self):
        self.start_link.set_active(self.start_node)
        self.end_link.set_active(self.end_node)

        chain_vector=self.end_link.other_node.matrix@self.end_link.other_point-self.start_link.other_node.matrix@self.start_link.other_point
        chain_target_vector=self.end_link.node.matrix@self.end_link.point-self.start_link.node.matrix@self.start_link.point

        origin=self.start_link.node.matrix@self.start_link.point

        axis=chain_vector.cross(chain_target_vector)
        angle=chain_vector.angle(chain_target_vector,0)

        for node in self.beam_nodes:
            self.rotate(origin,axis,angle,node.matrix)
            node.matrix.col[3][0:3]=node.matrix.to_translation()-chain_target_vector.normalized()*((chain_vector.length-chain_target_vector.length)/2)







        if chain_vector.length>chain_target_vector.length:

            chain_vector=self.end_link.other_node.matrix@self.end_link.other_point-self.start_link.other_node.matrix@self.start_link.other_point
            chain_target_vector=self.end_link.node.matrix@self.end_link.point-self.start_link.node.matrix@self.start_link.point

            max_length=0
            mass_center=None
            for node in self.beam_nodes:
                point_a,point_b=node.points

                max_length=max(max_length,(node.matrix@point_a-node.matrix@point_b).length)

                center=(point_a+point_b)/2
                if mass_center is None:
                    mass_center=node.matrix@center
                else:
                    mass_center+=node.matrix@center
            mass_center/=len(self.beam_nodes)

            start_point=self.start_link.other_node.matrix@self.start_link.other_point

            center_vector=mass_center-start_point

            shift_axis=mass_center-(start_point+chain_vector.normalized()*center_vector.length*math.cos(center_vector.angle(chain_vector,0)))

            # print(shift_axis.length)

            # shift_value=max_length
            # shift_value=max(max_length,(chain_vector.length**2-chain_target_vector.length**2)**0.5)
            # shift_value=(chain_vector.length**2-chain_target_vector.length**2)**0.5

            max_length=0.5
            shift_value=min(max_length,(chain_vector.length**2-chain_target_vector.length**2)**0.5)


            # for node in self.beam_nodes:
            #     node.matrix.col[3][0:3]=node.matrix.to_translation()+shift_axis.normalized()*shift_value
            #

    def inflate(self):

        beam_points={}
        for link in self.beam_links:
            beam_points[link.node_a]=[link.origin_a,link.point_a]
            beam_points[link.node_b]=[link.origin_b,link.point_b]
        beam_points[self.start_link.node_a]=[self.start_link.origin_a,self.start_link.point_a]
        beam_points[self.start_link.node_b]=[self.start_link.origin_b,self.start_link.point_b]

        beam_points[self.end_link.node_a]=[self.end_link.origin_a,self.end_link.point_a]
        beam_points[self.end_link.node_b]=[self.end_link.origin_b,self.end_link.point_b]


        beam_shifts=[]
        last_place=len(self.beam_nodes)-1
        beam_count=len(self.beam_nodes)
        for x in range(beam_count):

            if x==0:
                before_node=self.start_node
            else:
                before_node=self.beam_nodes[x-1]

            if x==last_place:
                after_node=self.beam_nodes[last_place]
            else:
                after_node=self.beam_nodes[x+1]

            node=self.beam_nodes[x]


            point_a=before_node.matrix@beam_points[before_node][0]
            point_b=before_node.matrix@beam_points[before_node][1]

            before_center=(point_a+point_b)/2
            before_radius=(point_a-point_b).length/2



            point_a=node.matrix@beam_points[node][0]
            point_b=node.matrix@beam_points[node][1]

            node_center=(point_a+point_b)/2
            node_radius=(point_a-point_b).length/2


            point_a=after_node.matrix@beam_points[after_node][0]
            point_b=after_node.matrix@beam_points[after_node][1]

            after_center=(point_a+point_b)/2
            after_radius=(point_a-point_b).length/2


            shift_vector=node_center-before_center
            before_shift=shift_vector.normalized()*max(0,(before_radius+node_radius)-shift_vector.length)
            # print(node,node_center,before_center)

            shift_vector=node_center-after_center
            after_shift=shift_vector.normalized()*max(0,(after_radius+node_radius)-shift_vector.length)

            # print(before_node,node,after_node)
            # print(node,before_shift,after_shift)

            # print(before_shift.angle(after_shift,0))

            if before_shift.length+after_shift.length!=0 :
                weight=1-before_shift.length/(before_shift.length+after_shift.length)
                try:
                    shift=before_shift.slerp(after_shift,weight)
                except:
                    shift=mathutils.Vector()
            else:
                shift=mathutils.Vector()
            shift=before_shift+after_shift



            beam_shifts.append(shift)

        min_length=1000
        for x in range(beam_count):
            min_length=min(min_length,beam_shifts[x].length)

        # print(min_length)
        for x in range(beam_count):
            beam_shifts[x]=beam_shifts[x].normalized()*min_length

        for x in range(beam_count):
            node=self.beam_nodes[x]
            shift=beam_shifts[x]

            node.matrix.col[3][0:3]=node.matrix.to_translation()+shift






    def align_segment(self,blanks):


        link,target,follower=blanks[0]

        before_matrix=follower.matrix.copy()

        link.track_to(target)

        for node in self.beam_nodes:
            if node is not follower:
                node.matrix[:]=follower.matrix@before_matrix.inverted()@node.matrix










    def solve_smooth(self,iterations=20,for_scene=False,for_frame=False):
        self.set_work_origins()

        if len(self.beam_nodes)==1:
            self.start_link.track_to(self.start_node,only_translate=True)
            self.end_link.track_to(self.end_node)
        elif len(self.beam_nodes)==2 :
            for link,target,follower in self.forward:
                link.track_to(target,only_translate=True)

            node_a=self.beam_nodes[0]
            matrix_a=node_a.matrix
            self.start_link.set_active(node_a)
            origin_a=self.start_link.point
            point_a=self.start_link.origin

            node_b=self.beam_nodes[1]
            matrix_b=node_b.matrix
            self.end_link.set_active(node_b)
            origin_b=self.end_link.origin
            point_b=self.end_link.point

            start_point=self.start_link.other_node.matrix@self.start_link.other_point
            end_point=self.end_link.other_node.matrix@self.end_link.other_point



            vt=end_point-start_point
            vc=matrix_b@point_b- matrix_a@origin_a

            axis=vc.cross(vt)
            angle=vc.angle(vt,0)
            self.rotate(start_point,axis,angle,matrix_a)
            self.rotate(start_point,axis,angle,matrix_b)

            va=matrix_a@point_a-matrix_a@origin_a
            vb=matrix_b@point_b-matrix_b@origin_b

            # print(va.length,vb.length)

            if vt.length>va.length+vb.length:
                self.rotate(start_point,va.cross(vt),va.angle(vt,0),matrix_a)
                self.rotate(start_point,vb.cross(vt),vb.angle(vt,0),matrix_b)
                for link,target,follower in self.forward:
                    link.track_to(target,only_translate=True)



            else:

                axis=vt.cross(va)
                angle=math.acos( min(1,((va.length**2+vt.length**2-vb.length**2)/(2*va.length*vt.length))) )-vt.angle(va,0)

                # print(angle)


                self.rotate(start_point,axis,angle,matrix_a)
                for link,target,follower in self.forward:
                    link.track_to(target,only_translate=True)
                self.end_link.track_to(self.end_node)


        else:

            iterations=round(len(self.beam_nodes)*2*iterations*0.2)


            if for_scene:
                factor=0.1
                tip_factor=0.3
                level=iterations*0.25
                if self.start_node.pose_level<=self.end_node.pose_level:blanks=self.forward
                else:blanks=self.backward
            if for_frame:
                factor=0.3
                tip_factor=0.3
                level=iterations*0.25
                if self.start_node.frame_level<=self.end_node.frame_level:blanks=self.forward
                else:blanks=self.backward



            # if for_frame:
            #     for node in self.beam_nodes:
            #         node.matrix[:]=node.source_rest_matrix

            for z in range(iterations*1):
                if z>level:
                    factor=1
                    tip_factor=1
                if True:
                    for blank_list,target_link,target_node in zip((self.forward,self.backward),(self.end_link,self.start_link),(self.end_node,self.start_node)):
                        for link,target,follower in blank_list:
                            link.track_to(target,only_translate=True)
                        if for_frame:
                            self.align()
                        for x in range(len(blank_list)):
                            link,target,follower=blank_list[x]
                            link.set_active(target)
                            origin=target.matrix@link.point

                            target_link.set_active(target_node)

                            target_point=target_link.node.matrix@target_link.point
                            current_point=target_link.other_node.matrix@target_link.other_point

                            current_vector=current_point-origin
                            target_vector=target_point-origin

                            axis=current_vector.cross(target_vector)

                            angle=current_vector.angle(target_vector,0)*factor
                            # angle=current_vector.angle(target_vector,0)*self.weights[x]

                            if x==0 or x==len(blank_list)-1:
                                angle*=tip_factor

                            for y in range(x,len(blank_list)):
                                link,target,follower=blank_list[y]
                                self.rotate(origin,axis,angle,follower.matrix)
                        if for_scene:
                            self.align()

            # if for_frame:
            #     for x in range(iterations):
            #         for link,target,follower in self.solve_blanks:
            #             link.track_to(target)


            for link,target,follower in blanks:
                link.track_to(target,only_translate=True)


        self.set_initial_origins()


    def solve_rope(self,iterations=20):
        self.set_work_origins()

        for x in range(iterations):
            for link,target,follower in self.solve_blanks:
                link.track_to(target)


        if self.start_node.pose_level<=self.end_node.pose_level:blanks=self.forward
        else: blanks=self.backward
        for link,target,follower in blanks:
            link.track_to(target,only_translate=True)

        self.set_initial_origins()

class NodeSolveData:
    def __init__(self):
        self.complex_linked_nodes=[]
        self.complex_links=[]


class NodeState:
    def __init__(self,node):
        self.transform=FullTransform(node)
        self.in_transform=FullTransform(node)
        self.out_transform=FullTransform(node)
        self.solved_transform=FullTransform(node)

        self.out_matrix=node.matrix.copy()
        self.in_matrix=node.matrix.copy()

        self.is_selected=node.is_selected
        self.is_pinned=node.is_pinned

        self.rotation_mode=node.rotation_mode

        self.pose_parent=None
        self.frame_parent=None


class Node:
    def __init__(self,node):
        self.source=node
        self.source_name=self.source.name
        self.is_used=False
        self.is_selected=False
        self.is_pinned=False
        self.is_transforming=False

        self.is_only_translated=False

        self.is_joint=False
        self.beam=False
        self.is_end=False

        self.is_simple=False

        self.links=None
        self.linked_nodes=None

        self.temp_linked_nodes=[]
        self.temp_links=[]

        self.scene=NodeSolveData()
        self.frame=NodeSolveData()

        self.pose_parent=None  #type: Node
        self.frame_parent=None  #type: Node
        self.pose_children=[]  #type: List[Node]
        self.frame_children=[]  #type: List[Node]
        self.level=0

        self.pose_level=0
        self.frame_level=0
        self.priority=0
        self.stretch_factor=0

        self.use_parent=False
        self.has_selected_parent=False
        self.selected_root=None
        self.is_selected_root=False
        self.has_transforming_parent=False
        self.transforming_root=None
        self.is_transforming_root=False
        self.is_translating=False
        self.is_rotating=False
        self.is_scaling=False
        self.is_armature_shift=False

        self.has_scaling_parent=False
        self.pose_parent_changed=False
        self.frame_parent_changed=False
        self.is_visible=True

        self.scaled_by_solver=False

        self.points=[]

        self.is_fixed=None

        self.cluster=None

        self.is_bone=(type(self.source)==bpy.types.PoseBone)

        if self.is_bone:
            if self.source.bone is None:
                self.fallback_points = (mathutils.Vector((0.0, 0.0, 0.0)),)
            else:
                self.fallback_points=(mathutils.Vector((0.0,0.0,0.0)),self.source.bone.matrix_local.inverted()@self.source.bone.tail_local)



            # self.fallback_points = (mathutils.Vector((0.0, 0.0, 0.0)), self.source.bone.matrix_local.inverted() @ self.source.bone.tail_local)
            # print(self.fallback_points)

            self.source_armature=self.source.id_data
            self.source_armature_name=self.source_armature.name
            self.matrix_local=self.source.bone.matrix_local
            self.armature_matrix_basis=self.source_armature.matrix_basis

            self.armature_location=self.source_armature.location
            self.armature_rotation_quaternion=self.source_armature.rotation_quaternion
            self.armature_rotation_euler=self.source_armature.rotation_euler
            self.armature_rotation_axis_angle=self.source_armature.rotation_axis_angle
            self.armature_scale=self.source_armature.scale



        else:
            self.fallback_points=(mathutils.Vector((0.0,0.0,0.0)),)
            self.source_armature=None
            self.source_armature_name=None
            self.matrix_local=None
            self.armature_matrix_basis=None

            self.armature_location=None
            self.armature_rotation_quaternion=None
            self.armature_rotation_euler=None
            self.armature_rotation_axis_angle=None
            self.armature_scale=None

        self.location=self.source.location
        self.rotation_quaternion=self.source.rotation_quaternion
        self.rotation_euler=self.source.rotation_euler
        self.rotation_axis_angle=self.source.rotation_axis_angle
        self.scale=self.source.scale

        self.local_quaternion=self.source.free_ik_local_quaternion
        self.local_euler=self.source.free_ik_local_euler
        self.local_axis_angle=self.source.free_ik_local_axis_angle

        self.rotation_mode=self.source.rotation_mode

        self.temp_location=None
        self.temp_rotation=None
        self.temp_scale=None

        matrix=self.get_matrix()

        self.matrix=matrix.copy()
        self.before_matrix=matrix.copy()
        self.temp_matrix=matrix.copy()
        self.rest_matrix=matrix.copy()
        self.work_rest_matrix=matrix.copy()
        self.source_rest_matrix=matrix.copy()
        self.copied_matrix=matrix.copy()
        self.clear_pose_matrix=matrix.copy()
        self.pose_rest_matrix=matrix.copy()
        self.frame_rest_matrix=matrix.copy()
        self.smooth_rest_matrix=matrix.copy()
        self.in_matrix=matrix.copy()
        self.modal_start_matrix=matrix.copy()
        self.frame_parented_matrix=matrix.copy()


        self.matrix_basis=self.source.matrix_basis.copy()


        self.initial_matrix=matrix.copy()
        self.initial_rest_matrix=None

        self.shift_matrix=mathutils.Matrix.Identity(4)

        self.transform=FullTransform(self)  #type: FullTransform

        self.modal_start_transform=FullTransform(self)  #type: FullTransform
        self.default_transform=FullTransform(self)  #type: FullTransform

        self.raw_transform=RawTransform(self)  #type: RawTransform
        self.last_raw_transform=RawTransform(self)  #type: RawTransform

        # self.transform.from_node()
        self.reference_rotation=self.transform.rotation.copy()
        self.reference_local_rotation=self.transform.local_rotation.copy()
        # self.reference_scale=self.raw_transform.get_reference_scale(self.transform)

        self.reference_scale=None


        # print(self.source.location)

        self.last=NodeState(self)

    def __str__(self):
        return self.source.name
        # return "{} {}".format(self.node_a.const_object,self.node_b.const_object)

    def __repr__(self):
        return self.__str__()

    def restore_from_name(self):
        if self.is_bone:
            self.source_armature=bpy.data.objects[self.source_armature_name]
            self.source=self.source_armature.pose.bones[self.source_name]
        else:
            self.source=bpy.data.objects[self.source_name]

    def restore_name(self):
        if self.is_bone:
            self.source_name=self.source.name
            self.source_armature_name=self.source.id_data.name
        else:
            self.source_name=self.source.name
            self.source_armature_name=None

    def get_matrix(self):
        if self.is_bone:
            return self.armature_matrix_basis@self.matrix_local@self.source.matrix_basis
            # return self.source.id_data.matrix_basis@self.source.bone.matrix_local@self.source.matrix_basis
        else:return self.source.matrix_basis.copy()
    def get_matrix_from_other(self,source):
        if self.is_bone:
            return source.id_data.matrix_basis@source.bone.matrix_local@source.matrix_basis
        else:return source.matrix_basis.copy()

    def get_parent(self,for_pose=False,for_frame=False):

        if for_pose: parent_name=gv.pose_parent_name
        if for_frame: parent_name=gv.frame_parent_name
        out_parent=None
        out_matrix=None

        if parent_name in self.source.constraints:
            target=self.source.constraints[parent_name].target
            subtarget=self.source.constraints[parent_name].subtarget
            out_matrix=self.source.constraints[parent_name].inverse_matrix
            if target is not None:
                if type(target.data)==bpy.types.Armature and subtarget!="":
                    key=target.pose.bones[subtarget]
                else:
                    key=target

                if key in gv.nodes_dictionary:
                    out_parent=gv.nodes_dictionary[key]
        if out_parent is not None:
            if out_parent.cluster!=self.cluster: out_parent=None

        if for_pose:
            self.pose_parent=out_parent
            if out_parent is not None: self.pose_rest_matrix[:]=out_matrix

        if for_frame:
            self.frame_parent=out_parent
            if out_parent is not None: self.frame_rest_matrix[:]=out_matrix


    def update_state_from_other(self,source):
        self.is_pinned=source.free_ik_is_pinned


    def update_state_frame(self):
        self.is_pinned=self.source.free_ik_is_pinned
        if self.is_pinned!=self.last.is_pinned:self.cluster.pinning_changed=True
        self.last.is_pinned=self.is_pinned


    def update_state_scene(self):
        #IS ACTIVE
        if self.is_bone:self.is_active=(bpy.context.mode=='POSE' and self.source==bpy.context.active_pose_bone)
        else:self.is_active=(self.source==bpy.context.object)

        #PRIORITY
        self.priority=self.source.free_ik.priority

        #STRETCH FACTOR
        self.stretch_factor=self.source.free_ik_stretch_factor

        #IS VISIBLE
        if self.is_bone:
            # self.is_visible=self.source_armature.visible_get() and not self.source.bone.hide and any([bl and al for bl,al in zip(self.source.bone.layers,self.source_armature.data.layers)])
            self.is_visible = self.source_armature.visible_get() and not self.source.bone.hide and (len(self.source.bone.collections) == 0 or any(collection.is_visible for collection in self.source.bone.collections))

        else:
            self.is_visible=self.source.visible_get()

        #IS PINNED
        self.is_pinned=self.source.free_ik_is_pinned
        if self.is_pinned!=self.last.is_pinned and self.cluster is not None: self.cluster.pinning_changed=True
        self.last.is_pinned=self.is_pinned

        #IS SELECTED

        if self.is_bone:
            self.is_selected=(bpy.context.mode=='POSE' and self.source.bone.select and self.source.id_data.select_get()) or (bpy.context.mode=='OBJECT' and self.source.id_data.select_get())
        else:
            self.is_selected=self.source.select_get()
        if self.is_selected!=self.last.is_selected and self.cluster is not None: self.cluster.selection_changed=True
        self.last.is_selected=self.is_selected

        #ROTATION MODE
        self.rotation_mode=self.source.rotation_mode
        if self.rotation_mode!=self.last.rotation_mode:
            self.transform.update_active_rotation()
            self.last.in_transform.update_active_rotation()
            self.last.solved_transform.update_active_rotation()
            self.last.out_transform.update_active_rotation()
            self.modal_start_transform.update_active_rotation()
            self.default_transform.update_active_rotation()
            self.raw_transform.update_active_rotation()
            self.last_raw_transform.update_active_rotation()
        self.last.rotation_mode=self.rotation_mode

        #POSE PARENT

        self.get_parent(for_pose=True)
        if self.pose_parent!=self.last.pose_parent and self.cluster is not None:
            self.cluster.pose_parent_changed=True
        self.last.pose_parent=self.pose_parent

        #FRAME PARENT
        self.get_parent(for_frame=True)
        if self.frame_parent!=self.last.frame_parent and self.cluster is not None:
            self.cluster.frame_parent_changed=True
        self.last.frame_parent=self.frame_parent


        #SOURCE REST MATRIX
        if self.is_bone:
            self.source_rest_matrix=self.source.id_data.matrix_basis@self.source.bone.matrix_local

    def update_color(self):
        if self.is_bone:
            if self.is_pinned:
                self.source.color.custom.normal=self.source.free_ik.pinned_color
                self.source.color.custom.select = bpy.context.preferences.themes[0].view_3d.bone_pose
                self.source.color.custom.active = bpy.context.preferences.themes[0].view_3d.bone_pose_active
            else:
                self.source.color.custom.normal = self.source.free_ik.color
                self.source.color.custom.select = bpy.context.preferences.themes[0].view_3d.bone_pose
                self.source.color.custom.active = bpy.context.preferences.themes[0].view_3d.bone_pose_active

            self.source.color.palette = 'CUSTOM'

        else:
            if self.is_pinned:
                self.source.color=*self.source.free_ik.pinned_color,1
            else:
                self.source.color = *self.source.free_ik.color,1





    def apply_parent(self):
        if self.pose_parent is not None and not self.is_armature_shift and not (
                self.is_pinned and not self.is_selected):

            out_location,out_rotation,out_scale=self.matrix.decompose()
            rest_location,rest_rotation,rest_scale=self.rest_matrix.decompose()

            parent_location,parent_rotation,parent_scale=self.pose_parent.matrix.decompose()
            parent_rest_location,parent_rest_rotation,parent_rest_scale=self.pose_parent.rest_matrix.decompose()

            if self.is_bone and (self.is_transforming or self.is_selected):

                if gv.is_pose_paste:
                    self.matrix[:]=self.pose_parent.matrix@self.pose_parent.copied_matrix.inverted()@self.copied_matrix
                    return

                if gv.is_clear_pose:


                    if gv.is_clear_rotation or gv.was_clear_rotation :
                        # out_rotation=parent_rotation@self.pose_parent.source_rest_matrix.inverted().to_quaternion()@out_rotation
                        out_rotation = parent_rotation @ self.pose_parent.source_rest_matrix.inverted().to_quaternion() @ self.source_rest_matrix.to_quaternion()

                    out_location=self.pose_parent.matrix@(self.pose_parent.source_rest_matrix.inverted()@self.source_rest_matrix).to_translation()
                    self.matrix[:]=compose_matrix((out_location,out_rotation,out_scale))
                    return

            if self.transforming_root is not None:
                root_location,root_rotation,root_scale=self.transforming_root.matrix.decompose()
                root_rest_location,root_rest_rotation,root_rest_scale=self.transforming_root.rest_matrix.decompose()

                if gv.inherit_scale:
                    if 0 not in root_rest_scale:
                        out_scale=mathutils.Vector(rest_scale[x]*root_scale[x]/root_rest_scale[x] for x in range(3))

                if gv.inherit_rotation:
                    # out_rotation=root_rotation@root_rest_rotation.inverted()@rest_rotation

                    # if self.is_transforming:
                    #     local_rotation=rest_rotation.inverted()@out_rotation
                    #     out_rotation=parent_rotation@parent_rest_rotation.inverted()@rest_rotation@local_rotation
                    # else:
                    #     out_rotation=parent_rotation@parent_rest_rotation.inverted()@rest_rotation

                    if self.is_transforming and gv.use_individual_origins and not (self.is_translating or self.is_scaling):
                        pass
                        out_rotation=parent_rotation@parent_rest_rotation.inverted()@out_rotation
                    else:
                        out_rotation=parent_rotation@parent_rest_rotation.inverted()@rest_rotation



                    # if gv.use_individual_origins and self.is_rotating:
                    #     out_rotation=parent_rotation@parent_rest_rotation.inverted()@out_rotation

                if gv.inherit_location:
                    out_location=self.pose_parent.matrix@(
                            self.pose_parent.rest_matrix.inverted()@self.rest_matrix).to_translation()

            self.matrix[:]=compose_matrix((out_location,out_rotation,out_scale))



    def apply_parent_simple(self):

        if self.pose_parent is not None :
            # if gv.is_pose_paste and self.is_bone:
            #     self.matrix[:]=self.pose_parent.matrix@self.pose_parent.copied_matrix.inverted()@self.copied_matrix
            #     return
            out_location,out_rotation,out_scale=self.matrix.decompose()
            rest_location,rest_rotation,rest_scale=self.rest_matrix.decompose()

            parent_location,parent_rotation,parent_scale=self.pose_parent.matrix.decompose()
            parent_rest_location,parent_rest_rotation,parent_rest_scale=self.pose_parent.rest_matrix.decompose()


            if gv.inherit_scale:
                if 0 not in parent_rest_scale:
                    out_scale=mathutils.Vector(rest_scale[x]*parent_scale[x]/parent_rest_scale[x] for x in range(3))

            if gv.inherit_rotation:
                out_rotation=parent_rotation@parent_rest_rotation.inverted()@rest_rotation

            if gv.inherit_location:
                out_location=self.pose_parent.matrix@(self.pose_parent.rest_matrix.inverted()@self.rest_matrix).to_translation()

            self.matrix[:]=compose_matrix((out_location,out_rotation,out_scale))


def get_mean_matrix(matrices):
    out_matrix=mathutils.Matrix.Identity(4)
    for x,matrix in enumerate(matrices,start=1):
        out_matrix=out_matrix.lerp(matrix,1/x)
    return out_matrix


def print_blank(*args):
    if type(args[0])==str:
        prefix=args[0]
        blank=args[1]
    else:
        blank=args[0]
        prefix=""

    link,target,follower=blank

    if target is None:
        print(prefix,f"{link.node_a}<->{link.node_b}  {link}")
    else:
        print(prefix,f"{target}<--{follower}  {link}")


class ClusterSceneData:
    def __init__(self):
        self.nodes=[]

        self.simple_blanks=[]
        self.limited_blanks=[]
        self.free_blanks=[]
        self.parent_blanks=[]
        self.complex_parent_blanks=[]

        self.complex_links=[]
        self.line_links=[]

        self.simple_nodes=[]
        self.complex_nodes=[]




class ClusterFrameData:
    def __init__(self):
        self.nodes=[]

        self.simple_blanks=[]
        self.complex_blanks=[]

        self.parent_blanks=[]

        self.complex_nodes=[]
        self.complex_links=[]

        self.line_links=[]


class Cluster:
    def __init__(self):

        self.nodes=[]
        self.links=[]



        self.frame=ClusterFrameData()
        self.scene=ClusterSceneData()


        self.pinning_changed=False
        self.selection_changed=False
        self.points_changed=False
        self.pose_parent_changed=False
        self.frame_parent_changed=False
        self.time_to_solve_scene=False
        self.time_to_solve_frame=False
        self.curve_changed=False
        self.was_changed=False

        self.has_twin_links=False

        self.is_transforming=False
        self.is_translating=False
        self.is_rotating=False
        self.is_scaling=False
        self.is_armature_shift=False

        self.time_to_solve_frame=False

        self.animation_data_changed=False




















    def update_state_scene(self):

        self.pinning_changed=False
        self.selection_changed=False
        self.points_changed=False
        self.pose_parent_changed=False
        self.frame_parent_changed=False


        for node in self.nodes:
            node.update_state_scene()
        for link in self.links:
            link.update_state_scene()

        if self.points_changed:
            for link in self.links:
                link.make_origins()

        if self.pose_parent_changed:
            self.update_scene_level()
        if self.frame_parent_changed:
            self.update_frame_level()

        if self.pinning_changed or self.frame_parent_changed :
            self.update_frame_level()
            self.make_frame_solve_data()

            self.update_scene_level()
            self.make_scene_solve_data()
        elif self.selection_changed or self.pose_parent_changed:
            self.update_scene_level()
            self.make_scene_solve_data()





        self.time_to_solve_frame=self.animation_data_changed and not gv.is_key_delete and not (gv.is_key_create or gv.is_indirect_key_create)

        # print("ANIMATION",self.animation_data_changed)
        # print(gv.is_indirect_key_create)
        # if gv.is_playback:
        #     return



        if self.time_to_solve_frame :
            for node in self.nodes:
                node.default_transform.apply_to_base()
                node.source.id_data.update_tag(refresh={'TIME'})
        elif gv.is_flip_quaternion:
            for node in self.nodes:
                if node.is_selected:
                    if node.source.rotation_mode=='QUATERNION':
                        node.source.free_ik_local_quaternion.negate()
                        node.last.out_transform.from_node()

        else:
            self.is_transforming=self.is_translating=self.is_rotating=self.is_scaling=self.is_armature_shift=False
            for node in self.nodes:
                node.transform.from_node()
                # if node.is_selected:
                #     print(node.transform.location)
                if gv.is_modal_transform and node.is_selected:


                    node.is_translating,node.is_rotating,node.is_scaling,node.is_armature_shift=node.transform.compare(node.last.out_transform)
                    if node.is_translating or node.is_rotating or node.is_scaling or node.is_armature_shift:
                        node.is_translating,placeholder,placeholder,placeholder=node.transform.compare(node.last.in_transform)


                else:
                    node.is_translating,node.is_rotating,node.is_scaling,node.is_armature_shift=node.transform.compare(node.last.out_transform)

                # node.is_translating,node.is_rotating,node.is_scaling,node.is_armature_shift=node.transform.compare(node.last.out_transform)

                node.last.in_transform.from_other(node.transform)
                node.is_transforming=node.is_translating or node.is_rotating or node.is_scaling or node.is_armature_shift

                # if node.is_selected:
                #     print(node.is_translating,node.is_rotating,node.is_scaling,node)
                    # print(node.transform.rotation)

                self.is_translating=self.is_translating or node.is_translating
                self.is_rotating=self.is_rotating or node.is_rotating
                self.is_scaling=self.is_scaling or node.is_scaling
                self.is_armature_shift=self.is_armature_shift or node.is_armature_shift
                self.is_transforming=self.is_transforming or node.is_transforming


                node.matrix[:]=node.get_matrix()

                if gv.is_clear_pose and node.is_selected:
                # if False :
                    # node.last.out_matrix[:]=node.clear_pose_matrix
                    out_location,out_rotation,out_scale=node.matrix.decompose()
                    rest_location,rest_rotation,rest_scale=node.source_rest_matrix.decompose()
                    if gv.was_clear_translation:out_location=rest_location
                    if gv.was_clear_rotation:out_rotation=rest_rotation
                    if gv.was_clear_scale:out_scale=rest_scale
                    node.matrix[:]=compose_matrix((out_location,out_rotation,out_scale))




                node.in_matrix[:]=node.matrix


            if gv.is_modal_transform:
                for node in self.nodes:
                    if node.is_selected:
                        node.is_translating=node.is_translating or self.is_translating
                        node.is_rotating = node.is_rotating or self.is_rotating
                        node.is_scaling = node.is_scaling or self.is_scaling

                        node.is_transforming = node.is_translating or node.is_rotating or node.is_scaling or node.is_armature_shift


            if self.is_transforming:
                self.update_transform_roots()
                if gv.is_pose_library:self.solve_frame()
                else:
                    self.solve_scene()
                for node in self.nodes:

                    node.reference_scale=node.transform.scale

                    if gv.solver_mode==gv.stretch:
                        if node.scaled_by_solver:
                            node.reference_scale=None
                    else:
                        if node.is_scaling:
                            node.reference_scale=None
                        if node.transforming_root is not None:
                            if node.transforming_root.is_scaling:
                                node.reference_scale=None

                    # print(node.reference_rotation,node.reference_local_rotation)

                    node.last.out_matrix[:]=node.matrix
                    node.last.out_transform.from_matrix(node.matrix)
                    node.last.out_transform.apply_to_base()
                    node.last.out_transform.apply_to_limit()
                    # if node.is_transforming:
                    node.default_transform.from_other(node.last.out_transform)


        if gv.is_key_delete:
            for node in gv.clustered_nodes:
                node.default_transform.from_other(node.last.out_transform)



    def update_state_frame(self):
        self.pinning_changed=False
        for node in self.nodes:
            node.update_state_frame()

        if self.pinning_changed or gv.links_changed:
            self.update_frame_level()
            self.make_frame_solve_data()



    def make_parent_blanks(self):
        # MAKE PARENT BLANKS

        fixed_nodes=[node for node in self.nodes if node.is_fixed]

        parent_blanks=[]

        for node in self.nodes:
            node.is_used=False
            node.complex_parent=None
            node.complex_parent_level=0
        while len(fixed_nodes)!=0:
            level=0
            fixed_nodes[0].is_used=True
            last_nodes=[fixed_nodes[0]]
            while len(last_nodes)!=0:

                next_nodes=set()
                for last_node in last_nodes:
                    last_node.complex_parent_level=level
                    for linked_node,link in zip(last_node.temp_linked_nodes,last_node.temp_links):
                        if not linked_node.is_used:
                            linked_node.is_used=True
                            if not linked_node.is_fixed:
                                next_nodes.add(linked_node)
                                linked_node.complex_parent=last_node
                            if not linked_node.is_fixed:
                                parent_blanks.append((link,last_node,linked_node))
                last_nodes=next_nodes
                level+=1

            fixed_nodes=[node for node in fixed_nodes if not node.is_used]
        return parent_blanks

    def make_solve_data(self,work_nodes):
        #UPDATE STATE

        #RESET

        simple_blanks=[]
        simple_nodes=[]

        line_links=[]
        complex_links=[]
        complex_blanks=[]

        for node in work_nodes:
            node.is_simple=False
            node.is_line=False
            node.is_used=False

        for link in self.links:
            link.is_simple=False
            link.is_line=False


        #UPDATE BEAMS JOINTS ENDS
        for node in work_nodes:
            node.is_joint=False
            node.is_beam=False
            node.is_end=False
            count=len(node.linked_nodes)

            if count==1:
                node.is_end=True
            if count==2:
                node.is_beam=True
            if count>2:
                node.is_joint=True

        # MAKE SIMPLE

        end_nodes={node for node in work_nodes if node.is_end and not node.is_fixed}
        # print(end_nodes)
        stages=[]
        while len(end_nodes)!=0:
            next_end_nodes=set()
            stage=[]
            for end_node in end_nodes:
                last_node=end_node
                last_node.is_used=True
                while last_node is not None:
                    last_node.is_used=True
                    next_node=None
                    for linked_node,link in zip(last_node.linked_nodes,last_node.links):
                        if not linked_node.is_used:
                            stage.append((link,linked_node,last_node))
                            last_node.is_simple=True
                            if not linked_node.is_fixed:
                                if linked_node.is_beam:
                                    next_node=linked_node
                                if linked_node.is_joint:
                                    next_end_nodes.add(linked_node)
                    last_node=next_node
            stages.append(stage)
            end_nodes=set()
            for next_end_node in next_end_nodes:
                is_end_node=False
                for linked_node in next_end_node.linked_nodes:
                    if not linked_node.is_used:
                        if is_end_node:
                            is_end_node=False
                            break
                        else:
                            is_end_node=True
                if is_end_node:
                    end_nodes.add(next_end_node)

        for stage in reversed(stages):
            for link,target,follower in reversed(stage):
                link.is_simple=True
                simple_blanks.append((link,target,follower))
                simple_nodes.append(follower)


        #UPDATE BEAMS AND JOINTS

        for node in work_nodes:
            node.is_joint=False
            node.is_beam=False
            if not node.is_simple:

                #IGNORE SIMPLE NODES
                count=0
                for linked_node in node.linked_nodes:
                    if not linked_node.is_simple:
                        count+=1
                if count==2:
                    node.is_beam=True
                if count>2:
                    node.is_joint=True

                #CONSIDER SIMPLE NODES
                # if len(node.linked_nodes)==2:node.is_beam=True
                # if len(node.linked_nodes)>2: node.is_joint=True




        # MAKE LINES

        start_nodes=[]
        for node in work_nodes:
            node.temp_links=[]
            node.temp_linked_nodes=[]
            if node.is_joint or node.is_fixed:
                start_nodes.append(node)
                node.is_used=True



        for start_node in start_nodes:
            for node,start_link in zip(start_node.linked_nodes,start_node.links):

                if not node.is_used and node.is_beam:
                    beam_nodes=[node]
                    beam_links=[]

                    end_node=None
                    end_link=None

                    last_node=node  # type:Node
                    while last_node is not None:
                        next_node=None
                        last_node.is_used=True
                        for linked_node,link in zip(last_node.linked_nodes,last_node.links):

                            if linked_node is not start_node and (linked_node.is_joint or linked_node.is_fixed):
                                end_node=linked_node
                                end_link=link
                            if linked_node.is_beam and not linked_node.is_used:
                                beam_nodes.append(linked_node)
                                beam_links.append(link)
                                next_node=linked_node
                        last_node=next_node
                    # print()
                    # print("START")
                    # print(start_node,beam_nodes,end_node)
                    # print(beam_links)

                    if len(beam_nodes)>=1:
                        for beam_node in beam_nodes:
                            beam_node.is_line=True
                        for beam_link in beam_links:
                            beam_link.is_line=True
                        start_link.is_line=True
                        end_link.is_line=True
                        line_link=LineLink(start_node,start_link,beam_nodes,beam_links,end_node,end_link)
                        complex_links.append(line_link)
                        line_links.append(line_link)

        # MAKE COMPLEX BLANKS

        for link in self.links:
            if not link.is_simple and not link.is_line:
                complex_links.append(link)
        for link in complex_links:
            link.node_a.temp_links.append(link)
            link.node_b.temp_links.append(link)

            link.node_a.temp_linked_nodes.append(link.node_b)
            link.node_b.temp_linked_nodes.append(link.node_a)


        complex_nodes=[node for node in work_nodes if not node.is_line and not node.is_simple]


        #TRANSLATION BLANKS

        complex_translation_blanks=[]

        last_nodes=[]
        for node in work_nodes:
            if node .is_fixed:
                last_nodes.append(node)
                node.is_used=True
            else:
                node.is_used=False


        while len(last_nodes)!=0:
            next_nodes=set()
            for last_node in last_nodes:
                for linked_node,link in zip(last_node.temp_linked_nodes,last_node.temp_links):
                    if not linked_node.is_used:
                        linked_node.is_used=True
                        complex_translation_blanks.append((link,last_node,linked_node))
                        next_nodes.add(linked_node)
            last_nodes=next_nodes



        return complex_links,line_links,simple_blanks,simple_nodes


        # print("MAKE SOLVE DATA")
        #
        # print("CLUSTER ",self)
        # print()
        # print(f"   SIMPLE {len(simple_blanks)}")
        # print("   ------")
        # for blank in simple_blanks:
        #     print_blank("    ",blank)
        #
        # print()
        # print(f"   COMPLEX {len(complex_blanks)}")
        # print("   -------")
        # for blank in complex_blanks:
        #     print_blank("    ",blank)
        # print()
        # print(f"   PARENT {len(parent_blanks)}")
        # print("   ------")
        # for blank in parent_blanks:
        #     print_blank("    ",blank)

        # print()
        # print("COMPLEX STRUCTURE")
        # for node in complex_nodes:
        #     print(node)
        #     for linked_node,link in zip(node.scene.complex_linked_nodes,node.scene.complex_links):
        #         print("    ",linked_node,link)

    def blanks_from_links(self,links):
        blanks=[]
        for link in links:
            if link.node_a.is_fixed and not link.node_b.is_fixed:
                blanks.append((link,link.node_a,link.node_b))
            elif link.node_b.is_fixed and not link.node_a.is_fixed:
                blanks.append((link,link.node_b,link.node_a))
            elif not link.node_b.is_fixed and not link.node_a.is_fixed:
                blanks.append((link,None,None))
        return blanks


    def make_translation_blanks(self,work_nodes,use_temp=False):
        translation_blanks=[]

        last_nodes=[]
        for node in work_nodes:
            if node.is_fixed:
                last_nodes.append(node)
                node.is_used=True
            else:
                node.is_used=False
        if len(last_nodes)==0 and len(work_nodes)!=0:
            last_nodes.append(work_nodes[0])


        while len(last_nodes)!=0:
            next_nodes=set()
            for last_node in last_nodes:
                if use_temp:
                    linked_nodes=last_node.temp_linked_nodes
                    links=last_node.temp_links
                else:
                    linked_nodes=last_node.linked_nodes
                    links=last_node.links

                for linked_node,link in zip(linked_nodes,links):
                    if not linked_node.is_used:
                        linked_node.is_used=True
                        translation_blanks.append((link,last_node,linked_node))
                        next_nodes.add(linked_node)
            last_nodes=next_nodes

        return translation_blanks


    def make_stretch_blanks(self,work_nodes):

        selected_joints=[]
        last_nodes=[]
        for node in work_nodes:
            if len(node.linked_nodes)>0:
                node.is_joint=True
                for linked_node in node.linked_nodes:
                    if linked_node.is_selected:
                        selected_joints.append(node)
                        break
            else:node.is_joint=False

            if node.is_selected:
                last_nodes.append(node)
                node.is_used=True
            else:node.is_used=False


            node.scaled_by_solver=False
            node.is_fixed=node.is_pinned and not node.is_selected


        for link in self.links:
            link.is_used=False


        stretch_blanks=[]

        for node in selected_joints:
            node.scaled_by_solver=True
            for linked_node,link in zip(node.linked_nodes,node.links):
                linked_node.scaled_by_solver=True
                if linked_node.is_selected:
                    stretch_blanks.append((link,linked_node,node))
            for linked_node,link in zip(node.linked_nodes,node.links):
                stretch_blanks.append((link,node,linked_node))



        # for node in self.scene.nodes:
        #     if node.is_selected:
        #         node.scaled_by_solver=True
        #         for linked_node,link in zip(node.linked_nodes,node.links):
        #             linked_node.scaled_by_solver=True
        #             if linked_node.is_selected:
        #                 stretch_blanks.append((link,linked_node,node))
        #         for linked_node,link in zip(node.linked_nodes,node.links):
        #             stretch_blanks.append((link,node,linked_node))
        #




        while len(last_nodes)!=0:
            next_nodes=set()
            for last_node in last_nodes:
                last_node.is_used=True
            for last_node in last_nodes:
                for linked_node,link in zip(last_node.linked_nodes,last_node.links):
                    if not link.is_used:
                        link.is_used=True

                        stretch_blanks.append((link,last_node,linked_node))
                        linked_node.scaled_by_solver=True


                        if not linked_node.is_used and linked_node.is_joint:
                            next_nodes.add(linked_node)

            last_nodes=next_nodes




        # for blank in stretch_blanks:
            # print_blank(blank)


        return stretch_blanks






    def make_scene_solve_data(self):

        # print("MAKE SOLVE DATA SCENE")


        #LIMITED
        has_pinned=False
        for node in self.nodes:
            if node.is_pinned and not node.is_selected:
                has_pinned=True
                break
        if not has_pinned:
            for node in self.nodes:
                node.is_fixed=False
                if node.pose_parent is None and len(node.pose_children)!=0:
                    node.is_fixed=True
                if node.is_selected or node.is_pinned:
                    node.is_fixed=True
        else:
            for node in self.nodes:
                node.is_fixed=node.is_selected or node.is_pinned

        # for node in self.nodes:
        #     node.is_fixed=node.is_selected or node.is_pinned

        self.scene.limited_links,self.scene.limited_line_links,self.scene.limited_simple_blanks,self.scene.limited_simple_nodes=self.make_solve_data(self.scene.nodes)
        self.scene.limited_simple_nodes.sort(key=lambda n:n.pose_level)

        for node in self.nodes:
            node.is_fixed=node.is_selected or node.is_pinned

        self.scene.limited_blanks=self.blanks_from_links(self.scene.limited_links)
        self.scene.limited_translation_blanks=self.make_translation_blanks(self.scene.nodes,use_temp=True)

        for node in self.scene.nodes:
            node.is_used=False

        self.scene.beam_nodes=[]
        for link in self.scene.limited_line_links:
            for node in link.beam_nodes:
                node.is_used=True
                self.scene.beam_nodes.append(node)
        self.scene.beam_nodes.sort(key=lambda n:n.pose_level)


        self.scene.usual_nodes=sorted([node for node in self.scene.nodes if not node.is_used],key=lambda n:n.pose_level)






        #FREE

        for node in self.nodes:
            node.is_fixed=node.is_pinned and not node.is_selected

        self.scene.free_blanks=self.blanks_from_links(self.scene.limited_links)
        self.scene.free_translation_blanks=self.make_translation_blanks(self.scene.nodes,use_temp=True)

        # self.scene.free_links,self.scene.free_line_links,self.scene.free_simple_blanks,self.scene.free_simple_nodes=self.make_solve_data(self.scene.nodes)
        # self.scene.free_simple_nodes.sort(key=lambda n:n.pose_level)
        #
        # # for node in self.nodes:
        # #     node.is_fixed=node.is_pinned and not node.is_selected
        # self.scene.free_blanks=self.blanks_from_links(self.scene.free_links)
        # self.scene.free_translation_blanks=self.make_translation_blanks(self.scene.nodes)
        #




        #PARENT

        self.scene.parent_blanks=[]

        links=sorted(self.links,key=lambda l: min(l.node_a.pose_level,l.node_b.pose_level))

        for link in links:

            if link.node_a.pose_level<=link.node_b.pose_level:
                target=link.node_a
                follower=link.node_b
            else:
                target=link.node_b
                follower=link.node_a

            if not follower.is_fixed:
                self.scene.parent_blanks.append((link,target,follower))

        #PINNED

        self.scene.pinned_blanks=[]

        pinned_nodes=[]
        for node in self.nodes:
            if node.is_pinned and not node.is_selected:
                pinned_nodes.append(node)
        for pinned_node in pinned_nodes:
            for pinned_linked_node,link in zip(pinned_node.linked_nodes,pinned_node.links):
                if pinned_linked_node.is_selected:
                    is_single=True
                    for selected_linked_node in pinned_linked_node.linked_nodes:
                        if selected_linked_node.is_selected:
                            is_single=False
                            break
                    if is_single:
                        self.scene.pinned_blanks.append((link,pinned_node,pinned_linked_node))


        #STRETCH
        self.scene.stretch_blanks=self.make_stretch_blanks(self.scene.nodes)






    def update_scene_level(self):

        for node in self.nodes:
            node.pose_children=[]

        for node in self.nodes:
            if node.pose_parent is not None:
                node.pose_parent.pose_children.append(node)

        last_nodes=[node for node in self.nodes if node.pose_parent is None and len(node.pose_children)!=0]
        level=0
        while len(last_nodes)!=0:
            next_nodes=[]
            for last_node in last_nodes:
                last_node.pose_level=level
                next_nodes.extend(last_node.pose_children)
            level+=1
            last_nodes=next_nodes

        for node in self.nodes:
            node.pose_level+=1/(1+node.priority)

        self.scene.nodes=sorted(self.nodes,key=lambda v:v.pose_level)

    def update_frame_level(self):



        for node in self.nodes:
            node.frame_children=[]
            node.get_parent(for_frame=True)


        for node in self.nodes:
            if node.frame_parent is not None:
                node.frame_parent.frame_children.append(node)

        last_nodes=[node for node in self.nodes if node.frame_parent is None and len(node.frame_children)!=0]
        level=0
        while len(last_nodes)!=0:
            next_nodes=[]
            for last_node in last_nodes:
                last_node.frame_level=level
                next_nodes.extend(last_node.frame_children)
            level+=1
            last_nodes=next_nodes

        for node in self.nodes:
            node.frame_level+=1/(1+node.priority)

        self.frame.nodes=sorted(self.nodes,key=lambda v:v.frame_level)


    def update_transform_roots(self):
        for node in self.scene.nodes:
            node.has_transforming_parent=False
            node.transforming_root=None

            if node.pose_parent is not None:
                if node.pose_parent.is_transforming and not node.pose_parent.has_transforming_parent:
                    node.transforming_root=node.pose_parent
                    node.has_transforming_parent=True
                    node.pose_parent.is_transforming_root=True
                if node.pose_parent.has_transforming_parent:
                    node.transforming_root=node.pose_parent.transforming_root
                    node.has_transforming_parent=True


    def solve_stretch(self):

        for node in self.nodes:
            if node.is_selected:
                if node.is_transforming and not (node.is_rotating or node.is_scaling):
                    rest_location,rest_rotation,rest_scale=node.modal_start_matrix.decompose()
                    location,rotation,scale=node.matrix.decompose()
                    node.matrix[:]=compose_matrix((location,rest_rotation,rest_scale))
            else:
                node.matrix[:]=node.modal_start_matrix




        for node in self.scene.nodes:
            if node.is_selected and node.is_bone and not (node.is_rotating or node.is_scaling) :
                if gv.stretch_mode in (gv.stretch_head, gv.stretch_tail):
                    node.scaled_by_solver=True
                    head=node.fallback_points[0]
                    tail=node.fallback_points[1]

                    head_points=[]
                    head_targets=[]
                    tail_points=[]
                    tail_targets=[]

                    for link in node.links:
                        link.set_active(node)

                        if (link.point-head).length<(link.point-tail).length:
                            head_points.append(link.point)
                            head_targets.append(link.other_node.matrix@link.other_point)
                        if (link.point-tail).length<=(link.point-head).length:
                            tail_points.append(link.point)
                            tail_targets.append(link.other_node.matrix@link.other_point)


                    if len(head_points)==0:
                        head_points.append(head)
                        if gv.is_modal_transform:head_targets.append(node.modal_start_matrix@head)
                        else:head_targets.append(node.last.out_matrix@head)
                    if len(tail_points)==0:
                        tail_points.append(tail)
                        if gv.is_modal_transform: tail_targets.append(node.modal_start_matrix@tail)
                        else:tail_targets.append(node.last.out_matrix@tail)

                    if gv.stretch_mode==gv.stretch_head:
                        points=tail_points
                        targets=tail_targets
                        origins=head_points
                    if gv.stretch_mode==gv.stretch_tail:
                        points=head_points
                        targets=head_targets
                        origins=tail_points
                        if gv.operator_changed:
                            node.matrix[:]=node.matrix@mathutils.Matrix.Translation(head-tail)


                    avg_point=None
                    for point in points:
                        if avg_point is None:avg_point=point.copy()
                        else:avg_point+=point
                    avg_point/=len(points)

                    avg_target=None
                    for target in targets:
                        if avg_target is None:avg_target=target.copy()
                        else:avg_target+=target
                    avg_target/=len(targets)

                    avg_origin=None
                    for origin in origins:
                        if avg_origin is None:avg_origin=origin.copy()
                        else:avg_origin+=origin
                    avg_origin/=len(origins)

                    to_point_scale(node.matrix,avg_point,avg_origin,avg_target,node.stretch_factor)



        for link,target,follower in self.scene.stretch_blanks:
            if follower.is_selected:
                link.track_to(target,only_translate=True)
            link.scale_to(target)
            link.track_to(target)

        for link,target,follower in self.scene.stretch_blanks:
            link.scale_to(target)
            link.track_to(target)




    def solve_smooth(self):

        # return

        # print("LIMITED")
        # print("COMPLEX BLANKS")
        # for blank in self.scene.limited_blanks:
        #     print_blank(blank)


        #
        # print("SIMPLE BLANKS")
        # for blank in self.scene.limited_simple_blanks:
        #     print_blank(blank)

        # print("TRANSLATION BLANKS")
        # for blank in self.scene.limited_translation_blanks:
        #     print_blank(blank)

        #
        # print("FREE BLANKS")
        # for blank in self.scene.free_blanks:
        #     print_blank(blank)

        # print("FREE LINKS")
        # for link in self.scene.free_links:
        #     print(link)

        # print("FREE SIMPLE BLANKS")
        # for blank in self.scene.free_simple_blanks:
        #     print_blank(blank)

        # print("TRANSLATION BLANKS")
        # for blank in self.scene.free_translation_blanks:
        #     print_blank(blank)
        #

        # print("LINES")
        # for link in self.scene.limited_line_links:
        #     print(link)


        # for node in self.nodes:
        #     print(node,(node.last.in_matrix.to_quaternion().inverted()@node.in_matrix.to_quaternion()).angle)


        #SET fLAGS

        for node in self.nodes:
            node.is_only_translated=gv.is_modal_transform and node.is_translating and not node.is_rotating
            node.is_fixed=node.is_pinned or node.is_selected

        if gv.is_modal_transform:
            for node in self.scene.usual_nodes:
                node.rest_matrix[:]=node.last.out_matrix
                node.matrix[:]=node.modal_start_matrix

            for node in self.scene.beam_nodes:
                node.rest_matrix[:]=node.last.out_matrix
                node.matrix[:]=node.last.out_matrix

            for node in self.scene.beam_nodes:
                node.apply_parent()

            for node in self.scene.nodes:
                node.rest_matrix[:]=node.matrix
                if node.is_transforming:node.matrix[:]=node.in_matrix
                else:node.matrix[:]=node.rest_matrix
        else:
            for node in self.scene.nodes:
                node.rest_matrix[:]=node.last.out_matrix

        # for node in self.scene.nodes:
        #     if gv.is_modal_transform and node.is_selected:
        #         node.rest_matrix[:]=node.modal_start_matrix
        #     else:
        #         node.rest_matrix[:]=node.last.out_matrix

        #APPLY PARENTS

        for node in self.scene.nodes:
            node.apply_parent()





        for link,target,follower in self.scene.parent_blanks:
            if not follower.is_translating:
                link.track_to(target,only_translate=True)

        for link,target,follower in self.scene.pinned_blanks:
            link.track_to(target,only_translate=True)



        #UPDATE LINKS

        for link in self.links:
            link.update_length()

        for link in self.scene.limited_line_links:
            link.prepare()

        iterations=gv.scene_iterations
        if gv.operator_changed:
            iterations*=3
        # print(iterations)

        #SOLVE LIMITED


        for x in range(iterations):
            for link,target,follower in self.scene.limited_blanks:
                # print_blank([link,target,follower])
                link.track_to(target)
            if x==0:
                for link,target,follower in self.scene.limited_translation_blanks:
                    link.track_to(target,only_translate=True)





        # for node in self.scene.beam_nodes:
        #     node.apply_parent()

        # return

        error=0
        for link in self.scene.limited_links:
            error=max(error,link.get_error())


        if error>0.01 or True:
            # print('ERROR')
            #SOLVE FREE
            for x in range(iterations):
                for link,target,follower in self.scene.free_blanks:
                    link.track_to(target)
                if x==0:
                    for link,target,follower in self.scene.free_translation_blanks:
                        link.track_to(target,only_translate=True)



            #RESTORE
            for node in self.scene.nodes:
                if not node.is_transforming and not node.is_selected:
                    node.matrix[:]=node.rest_matrix
            for node in self.scene.nodes:
                if not node.is_transforming:
                    node.apply_parent()

            #SOLVE LIMITED
            for x in range(iterations):
                for link,target,follower in self.scene.limited_blanks:
                    link.track_to(target)
                if x==0:
                    for link,target,follower in self.scene.limited_translation_blanks:
                        link.track_to(target,only_translate=True)



        for link in self.scene.limited_line_links:
            link.solve_smooth(iterations,for_scene=True)

        if not gv.is_pose_paste:
            for node in self.scene.nodes:
                node.rest_matrix[:]=node.last.out_matrix

            for node in self.scene.limited_simple_nodes:
                node.matrix[:]=node.rest_matrix

            for node in self.scene.limited_simple_nodes:
                node.apply_parent_simple()
        for link,target,follower in self.scene.limited_simple_blanks:
            link.track_to(target,only_translate=True)



    def solve_rope(self):

        # print("SOLVE SCENE")
        # return



        #SET fLAGS

        for node in self.nodes:
            node.is_only_translated=gv.is_modal_transform and node.is_translating and not node.is_rotating
            node.is_fixed=node.is_pinned or node.is_selected

        #RESTORE TRANSFORM
        for node in self.scene.nodes:
            # node.rest_matrix[:]=node.last.out_matrix
            node.modal_start_matrix[:]=node.last.out_matrix

        for node in self.scene.nodes:
            node.apply_parent()



        for link,target,follower in self.scene.parent_blanks:
            if not follower.is_translating:
                link.track_to(target,only_translate=True)


        for link,target,follower in self.scene.pinned_blanks:
            link.track_to(target,only_translate=True)



        #UPDATE LINKS

        for link in self.links:
            link.update_length()

        for link in self.scene.limited_line_links:
            link.prepare()


        iterations=gv.scene_iterations
        if gv.operator_changed:
            iterations*=3

        for x in range(iterations):
            for link,target,follower in self.scene.limited_blanks:
                link.track_to(target)
            if x==0:
                for link,target,follower in self.scene.limited_translation_blanks:
                        link.track_to(target,only_translate=True)




        error=0
        for link in self.scene.limited_links:
            error=max(error,link.get_error())

        if error>0.01 and True:
            # print('ERROR')

            for x in range(iterations):
                for link,target,follower in self.scene.free_blanks:
                    link.track_to(target)
                if x==0:
                    for link,target,follower in self.scene.free_translation_blanks:
                        link.track_to(target,only_translate=True)

            for node in self.scene.nodes:
                if not node.is_transforming:
                    node.matrix[:]=node.last.out_matrix

            for x in range(iterations):
                for link,target,follower in self.scene.limited_blanks:
                    link.track_to(target)
                if x==0:
                    for link,target,follower in self.scene.limited_translation_blanks:
                        link.track_to(target,only_translate=True)

        for link in self.scene.limited_line_links:
            link.solve_rope(iterations)

        if not gv.is_pose_paste:
            for node in self.scene.limited_simple_nodes:
                node.matrix[:]=node.rest_matrix
            for node in self.scene.limited_simple_nodes:
                node.apply_parent_simple()



        for link,target,follower in self.scene.limited_simple_blanks:
            link.track_to(target)


        # for node in self.nodes:
        #     node.rest_matrix[:]=node.matrix





    def solve_scene(self):
        # print("SOLVE SCENE")
        if gv.solver_mode==gv.smooth:
            self.solve_smooth()
        elif gv.solver_mode==gv.rope:
            self.solve_rope()
        elif gv.solver_mode==gv.stretch:
            if gv.is_clear_pose or gv.is_pose_paste:
                self.solve_smooth()
            else:
                self.solve_stretch()

    def make_frame_solve_data(self):
        # print("MAKE SOLVE DATA FRAME")
        self.update_frame_level()
        self.frame.has_pinned=False
        for node in self.frame.nodes:
            node.is_fixed=node.is_pinned
            if node.is_pinned:
                self.frame.has_pinned=True




        complex_links,self.frame.line_links,self.frame.simple_blanks,self.frame.simple_nodes=self.make_solve_data(self.frame.nodes)
        self.frame.complex_blanks=self.blanks_from_links(complex_links)



        self.frame.complex_translation_blanks=self.make_translation_blanks(self.frame.nodes,use_temp=True)


        for node in self.nodes:
            node.frame_pinned_root=None
            node.frame_root=None
            node.is_frame_root=False

        for node in self.frame.nodes:
            if node.frame_parent is None and len(node.frame_children)!=0:
                pinned_root=None
                last_nodes=[node]
                children=[node]
                while len(last_nodes)!=0:
                    next_nodes=[]
                    for last_node in last_nodes:
                        if last_node.is_pinned and pinned_root is None:
                            pinned_root=last_node

                        next_nodes.extend(last_node.frame_children)
                        children.extend(last_node.frame_children)
                    last_nodes=next_nodes
                for child in children:
                    child.frame_root=node
                    child.frame_pinned_root=pinned_root

        for node in self.frame.nodes:
            node.is_fixed=False
            if node.frame_pinned_root is not None or node.is_pinned:
                node.is_fixed=True

        self.frame.translation_blanks=self.make_translation_blanks(self.frame.nodes,use_temp=False)


        #PARENT

        self.frame.parent_blanks=[]

        for node in self.frame.nodes:
            if node.frame_parent is None and len(node.frame_children)!=0 and node.frame_pinned_root is not None:
                last_nodes={node}
                while len(last_nodes)!=0:
                    next_nodes=set()
                    for last_node in last_nodes:
                        for linked_node,link in zip(last_node.linked_nodes,last_node.links):
                            if linked_node.frame_parent is last_node:
                                if not linked_node.is_pinned:
                                    self.frame.parent_blanks.append((link,last_node,linked_node))
                                next_nodes.add(linked_node)


                    last_nodes=next_nodes






    def solve_frame(self):

        # print("SOLVE FRAME")
        # self.update_frame_level()



        #
        # for node in self.frame.nodes:
        #
        #     l,r,s=node.matrix.decompose()
        #
        #     if node.frame_parent is not None:
        #         node.frame_parented_matrix[:]=compose_matrix((l,node.frame_parent.temp_rotation@to_quaternion(node.transform.local_rotation),s))
        #
        #     else:
        #         node.frame_parented_matrix[:]=node.matrix
        #
        #
        #     node.temp_location,node.temp_rotation,node.temp_scale=node.frame_parented_matrix.decompose()
        #     node.matrix[:]=node.frame_parented_matrix




        for node in self.frame.nodes:
            if node.frame_parent is None and len(node.frame_children)!=0:
                node.frame_parented_matrix[:]=node.matrix
                last_nodes=[node]
                while len(last_nodes)!=0:
                    next_nodes=[]
                    for last_node in last_nodes:
                        if last_node.is_pinned:
                            parent_rotation=last_node.matrix.to_quaternion()
                        else:
                            parent_rotation=last_node.frame_parented_matrix.to_quaternion()
                            last_node.matrix[:]=last_node.frame_parented_matrix

                        for child in last_node.frame_children:

                            l,r,s=child.matrix.decompose()
                            child.frame_parented_matrix[:]=compose_matrix((l,parent_rotation@to_quaternion(child.transform.local_rotation),s))

                        next_nodes.extend(last_node.frame_children)
                    last_nodes=next_nodes






        for node in self.frame.nodes:
            if node.frame_pinned_root is not None and not node.is_pinned:
                if node.frame_level<node.frame_pinned_root.frame_level:

                    node.matrix[:]=node.frame_pinned_root.matrix@node.frame_pinned_root.frame_parented_matrix.inverted()@node.frame_parented_matrix



        if not self.frame.has_pinned:
            before_matrices=[node.matrix.copy() for node in self.frame.nodes]



        iterations=gv.frame_iterations
        if True:
            for link in self.links:
                link.update_length()

            for link in self.frame.line_links:
                link.prepare()

            for link,target,follower in self.frame.parent_blanks:
                link.track_to(target,only_translate=True)
            for link,target,follower in self.frame.translation_blanks:
                link.track_to(target,only_translate=True)

            for link,target,follower in self.frame.complex_translation_blanks:
                if not follower.is_pinned:
                    link.track_to(target,only_translate=True)



            for x in range(iterations):
                for link,target,follower in self.frame.complex_blanks:
                    link.track_to(target)
            for link in self.frame.line_links:
                link.solve_smooth(iterations,for_frame=True)
            for link,target,follower in self.frame.simple_blanks:
                link.track_to(target,only_translate=True)




        if not self.frame.has_pinned:
            matrices=[node.matrix for node in self.frame.nodes]
            cluster_matrix=get_mean_matrix(matrices)
            cluster_matrices=[before_matrix@(matrix.inverted_safe()@cluster_matrix) for before_matrix,matrix in zip(before_matrices,matrices)]

            cluster_shift=cluster_matrix.inverted_safe()@get_mean_matrix(cluster_matrices)

            m=cluster_matrix@cluster_shift@cluster_matrix.inverted_safe()

            for node in self.nodes:
                node.matrix[:]=m@node.matrix








def time_to_make_links():
    group=bpy.context.scene.free_ik.group
    if group is None:
        gv.last_group_state=[]
        return False

    if gv.time_to_force_rebuild:
        gv.time_to_force_rebuild=False
        return True

    if len(gv.last_group_state)!=len(group.objects):
        return True

    for state,group_object in zip(gv.last_group_state,group.objects):
        if state!=(group_object,group_object.free_ik.node_a,group_object.free_ik.node_b):
            return True

    return False


def make_links():
    gv.links=[]

    gv.nodes_dictionary={}
    gv.links_dictionary={}
    for source in bpy.context.scene.free_ik.group.objects:
        link=Link(source)
        if link.is_valid():
            gv.links.append(link)
            gv.links_dictionary[link.source]=link
            gv.nodes_dictionary[link.node_a]=Node(link.node_a)
            gv.nodes_dictionary[link.node_b]=Node(link.node_b)
    for link in gv.links:
        link.node_a=gv.nodes_dictionary[link.node_a]
        link.node_b=gv.nodes_dictionary[link.node_b]
        link.nodes=(link.node_a,link.node_b)

    gv.nodes=list(gv.nodes_dictionary.values())

    gv.last_group_state=[(source,source.free_ik.node_a,source.free_ik.node_b) for source in
                         bpy.context.scene.free_ik.group.objects]

    # print("UPDATE LINKS")
    # print("NODES:",len(gv.nodes),"LINKS:",len(gv.links))


def reset_structure():
    gv.nodes=[]
    gv.clustered_nodes=[]
    gv.nodes_dictionary={}
    gv.links_dictionary={}
    gv.links=[]
    gv.clusters=[]
    gv.last_group_state=[]
    gv.last_operator=None



def validate_frame():
    # print("VALIDATE FRAME")
    gv.links_changed=False
    for link in gv.links:
        link.update_state_frame()

    if gv.links_changed:
        # print("LINKS CHANGED")
        make_clusters()
        for cluster in gv.clusters:
            cluster.update_state_frame()



def validate_structure():
    if bpy.context.scene.free_ik.group is not None:
        if time_to_make_links():
            reset_structure()
            make_links()
            make_clusters()
            read_animation_data()

            for cluster in gv.clusters:
                cluster.update_scene_level()
                cluster.make_scene_solve_data()

                cluster.update_frame_level()
                cluster.make_frame_solve_data()

        else:
            gv.links_changed=False
            for link in gv.links:
                link.update_state_scene()

            if gv.links_changed or gv.is_after_frame:
                make_clusters()
                for cluster in gv.clusters:
                    cluster.update_scene_level()
                    cluster.make_scene_solve_data()

                    cluster.update_frame_level()
                    cluster.make_frame_solve_data()




            # for cluster in gv.clusters:
            #     for node in cluster.nodes:
            #         node.transform.from_node()
            #         node.transform.apply_to_limit()
            #         node.transform.apply_to_base()



def update_reference():
    pass

    id_objects=[]
    for id_object in gv.id_object_cluster_dictionary:
        id_object.update_tag(refresh={'TIME'})
        id_objects.append(id_object)
        if type(id_object.data)==bpy.types.Armature:
            for pose_bone in id_object.pose.bones:
                id_objects.append(pose_bone)

    gv.id_object_state_dictionary={}
    object_properties=bpy.types.Object.bl_rna.properties.keys()
    pose_bone_properties=bpy.types.PoseBone.bl_rna.properties.keys()

    for id_object in id_objects:
        if type(id_object)==bpy.types.Object:work_properties=object_properties
        if type(id_object)==bpy.types.PoseBone:work_properties=pose_bone_properties

        customs=id_object.keys()

        values={}
        custom_values={}


        for work_property in work_properties:
            try:value=getattr(id_object,work_property)
            except:value=None
            values[work_property]=value

        for custom in customs:
            try:value=id_object[custom]
            except:value=None
            custom_values[custom]=value

        gv.id_object_state_dictionary[id_object]=values,custom_values

def restore_state():
    pass
    # for id_object,state in gv.id_object_state_dictionary:
    #     values,custom_values=state
    #
    #     for key,value in values.items():
    #         try:setattr(id_object,key,value)
    #         except:pass
    #     for key,value in custom_values.items():
    #         try:id_object[key]=value
    #         except:pass


def read_animation_data():
    gv.id_object_cluster_dictionary={}
    gv.id_object_animation_dictionary={}
    for cluster in gv.clusters:
        for node in cluster.nodes:
            id_object=node.source.id_data
            if id_object in gv.id_object_cluster_dictionary:
                gv.id_object_cluster_dictionary[node.source.id_data].add(cluster)
            else:
                gv.id_object_cluster_dictionary[node.source.id_data]={cluster}

    update_animation_data()



def update_animation_data():
    for cluster in gv.clusters:
        cluster.animation_data_changed=False


    frame=bpy.context.scene.frame_current

    for id_object in gv.id_object_cluster_dictionary:
        curve_data=[]
        nla_data=[]

        if id_object.animation_data is not None:
            if id_object.animation_data.action is not None:
                for curve in id_object.animation_data.action.fcurves:
                    group_data=None
                    if curve.group is not None:
                        group_data=(curve.group.lock,curve.group.show_expanded,curve.group.show_expanded_graph)
                    curve_data.append((curve.evaluate(frame),curve.extrapolation,curve.hide,curve.mute,curve.lock,group_data))


            for nla_track in id_object.animation_data.nla_tracks:
                strip_data=[]

                nla_data.append((nla_track.is_solo,nla_track.lock,nla_track.mute,strip_data))
                for strip in nla_track.strips:
                    strip_data.append((strip.action_frame_end,strip.action_frame_start,strip.blend_in,strip.blend_out,strip.blend_type,strip.extrapolation,strip.frame_start,strip.frame_end,strip.influence,strip.mute,strip.repeat,strip.scale,strip.strip_time,strip.use_animated_influence,strip.use_animated_time,strip.use_animated_time_cyclic,strip.use_auto_blend,strip.use_reverse,strip.use_sync_length   ))


        animation=[curve_data,nla_data]
        if id_object in gv.id_object_animation_dictionary:
            if gv.id_object_animation_dictionary[id_object]!=animation:
                for cluster in gv.id_object_cluster_dictionary[id_object]:
                    cluster.animation_data_changed=True


        gv.id_object_animation_dictionary[id_object]=animation





def update_drivers():
    for node in gv.nodes:
        if node.source.id_data.animation_data is not None:
            for driver in node.source.id_data.animation_data.drivers:
                driver.driver.expression+=""


def set_limits_state(state):
    for node in gv.nodes:
        if gv.limit_location_name in node.source.constraints:
            node.source.constraints[gv.limit_location_name].mute=not (state and node.source.free_ik.is_rig_enabled)
        if gv.limit_rotation_name in node.source.constraints:
            node.source.constraints[gv.limit_rotation_name].mute=not (state and node.source.free_ik.is_rig_enabled)
        if gv.limit_scale_name in node.source.constraints:
            node.source.constraints[gv.limit_scale_name].mute=not (state and node.source.free_ik.is_rig_enabled)
        node.source.id_data.update_tag(refresh={'OBJECT','DATA','TIME'})


def make_clusters():
    for node in gv.nodes:
        node.is_used=False
        node.cluster=None
        node.links=[]
        node.linked_nodes=[]
        node.temp_links=[]
        node.temp_linked_nodes=[]

        node.points=[]

        node.has_twin_links=False

    active_links=[]

    for link in gv.links:
        link.is_used=False
        link.cluster=None
        if link.is_enabled and link.node_a is not link.node_b:
            if link.node_a.source.free_ik.is_rig_enabled and link.node_b.source.free_ik.is_rig_enabled:
                active_links.append(link)
                link.node_a.points.append(link.point_a)
                link.node_b.points.append(link.point_b)

    for link in active_links:
        link.make_origins()

    link_count=len(active_links)
    for x in range(link_count):

        if not active_links[x].is_used:
            twin_links=[active_links[x]]
            for y in range(x+1,link_count):
                if active_links[x].is_twin(active_links[y]):
                    active_links[y].is_used=True
                    twin_links.append(active_links[y])

            if len(twin_links)==1:
                out_link=active_links[x]

                out_link.node_a.links.append(out_link)
                out_link.node_b.links.append(out_link)

                out_link.node_a.linked_nodes.append(out_link.node_b)
                out_link.node_b.linked_nodes.append(out_link.node_a)



    gv.clusters=[]

    for node in gv.nodes:
        if not node.is_used and len(node.linked_nodes)!=0:
            cluster=Cluster()
            gv.clusters.append(cluster)

            node.is_used=True
            node.cluster=cluster
            cluster.nodes.append(node)

            last_nodes=[node]  #type: List[Node]
            while len(last_nodes)!=0:
                next_nodes=set()
                for last_node in last_nodes:
                    for linked_node in last_node.linked_nodes:
                        if not linked_node.is_used:
                            linked_node.is_used=True
                            linked_node.cluster=cluster
                            cluster.nodes.append(linked_node)
                            next_nodes.add(linked_node)

                last_nodes=next_nodes
            link_set=set()
            for cluster_node in cluster.nodes:

                for link in cluster_node.links:
                    link.cluster=cluster
                    link_set.add(link)
            cluster.links=list(link_set)

    gv.clustered_nodes=[node for node in gv.nodes if node.cluster is not None]

    # for node in gv.clustered_nodes:
    #     node.is_end=node.is_beam=node.is_joint=False
    #     if len(node.linked_nodes)==1:
    #         node.is_end=True
    #     if len(node.linked_nodes)==2:
    #         node.is_beam=True
    #     if len(node.linked_nodes)>2:
    #         node.is_joint=True

    # print()
    # print("MAKE CLUSTERS")
    # print("CLUSTERS:",len(gv.clusters),"NODES:",len(gv.nodes),"LINKS:",len(gv.links))
    # print("CLUSTERED NODES:",len(gv.clustered_nodes))
    # print()
    # for x,cluster in enumerate(gv.clusters):
    #     print(f"CLUSTER {x}")
    #     print()
    #     print(f"    NODES {len(cluster.nodes)}")
    #     print("    -----")
    #     for node in cluster.nodes:
    #         print("   ",node.source.name)
    #     print()
    #     print(f"    LINKS {len(cluster.links)}")
    #     print("    -----")
    #     for link in cluster.links:
    #         print("   ",link)


def update(self):
    bpy.context.object.update_tag(refresh={'OBJECT','DATA','TIME'})
    return 1,2,3,4


ui_extenders=set()



def register_extensions():
    bpy.types.Object.free_ik=bpy.props.PointerProperty(type=FreeIKNodeSettings)
    bpy.types.Object.free_ik_is_pinned=bpy.props.BoolProperty(name="Pinned",default=False)
    bpy.types.Object.free_ik_stretch_factor=bpy.props.FloatProperty(name="Stretch factor",default=0)

    bpy.types.Object.free_ik_local_quaternion=bpy.props.FloatVectorProperty(name="Local rotation",subtype='QUATERNION',size=4,default=(1,0,0,0))
    bpy.types.Object.free_ik_local_euler=bpy.props.FloatVectorProperty(name="Local rotation",subtype='EULER',size=3)
    bpy.types.Object.free_ik_local_axis_angle=bpy.props.FloatVectorProperty(name="Local rotation",subtype='AXISANGLE',size=4)

    bpy.types.PoseBone.free_ik=bpy.props.PointerProperty(type=FreeIKNodeSettings)
    bpy.types.PoseBone.free_ik_is_pinned=bpy.props.BoolProperty(name="Pinned",default=False)
    bpy.types.PoseBone.free_ik_stretch_factor=bpy.props.FloatProperty(name="Stretch factor",default=0)
    bpy.types.PoseBone.free_ik_was_connected=bpy.props.BoolProperty(name="Was connected",default=False)

    bpy.types.PoseBone.free_ik_local_quaternion=bpy.props.FloatVectorProperty(name="Local rotation",subtype='QUATERNION',size=4,default=(1,0,0,0))
    bpy.types.PoseBone.free_ik_local_euler=bpy.props.FloatVectorProperty(name="Local rotation",subtype='EULER',size=3)
    bpy.types.PoseBone.free_ik_local_axis_angle=bpy.props.FloatVectorProperty(name="Local rotation",subtype='AXISANGLE',size=4)

    bpy.types.Scene.free_ik=bpy.props.PointerProperty(type=FreeIKSceneSettings)
    bpy.types.Scene.free_ik_gv=gv

    bpy.types.PoseBone.matrix_world=property(pose_bone_world_matrix_get,pose_bone_world_matrix_set)

    # bpy.types.PoseBone.select = property(pose_bone_select_get,pose_bone_select_set)

    # bpy.types.VIEW3D_PT_overlay_pose.append(show_overlays_draw)
    bpy.types.BONE_PT_transform.append(bone_transform_extender)
    bpy.types.OBJECT_PT_transform.append(object_transform_extender)


def unregister_extensions():
    del bpy.types.Scene.free_ik_gv
    bpy.types.BONE_PT_transform.remove(bone_transform_extender)
    bpy.types.OBJECT_PT_transform.remove(object_transform_extender)


def pose_bone_world_matrix_get(pose_bone):
    return pose_bone.id_data.matrix_world@pose_bone.matrix


def pose_bone_world_matrix_set(pose_bone,matrix):
    pose_bone.matrix=pose_bone.id_data.matrix_world.inverted()@matrix


def pose_bone_select_get(pose_bone):
    return pose_bone.bone.select


def pose_bone_select_set(pose_bone,other):
    pose_bone.bone.select=other


def update_parents():
    pass  #print("UPDATE PARENTS")
    for cluster in gv.clusters:
        for node in cluster.nodes:
            node.pose_parent=node.get_parent(for_pose=True)
            node.frame_parent=node.get_parent(for_frame=True)
            if node.frame_parent is None:
                node.pin_priority=len(gv.nodes)+node.priority
            else:
                node.pin_priority=node.frame_level


def update_state():
    pass  #print("UPDATE STATE")
    pass
    gv.inherit_location=bpy.context.scene.free_ik.inherit_location
    gv.inherit_rotation=bpy.context.scene.free_ik.inherit_rotation
    gv.inherit_scale=bpy.context.scene.free_ik.inherit_scale
    gv.inherit_any=gv.inherit_location or gv.inherit_rotation or gv.inherit_scale

    gv.use_individual_origins=(bpy.context.scene.tool_settings.transform_pivot_point=='INDIVIDUAL_ORIGINS')

    for node in gv.nodes:
        node.update_state()
    for link in gv.links:
        link.update_state()


def shrink(link: Link,only_translate=False):
    point_a=link.point_a
    point_b=link.point_b
    matrix_a=link.node_a.matrix
    matrix_b=link.node_b.matrix

    origin_a=link.origin_a
    origin_b=link.origin_b

    target_point_world=(matrix_a@point_a+matrix_b@point_b)/2

    matrices=(matrix_a,matrix_b)
    origins=(origin_a,origin_b)
    points=(point_a,point_b)

    for x in range(2):
        if not link.nodes[x].is_fixed:
            matrix=matrices[x]
            origin=origins[x]
            point=points[x]

            own_point_world=matrix@point
            origin_world=matrix@origin

            if not only_translate:

                parent_matrix=mathutils.Matrix.Identity(4)
                parent_matrix.col[3][0:3]=origin_world

                parent_inverted=parent_matrix.inverted()

                fallback=0
                current_vector=parent_inverted@own_point_world
                target_vector=parent_inverted@target_point_world

                angle=current_vector.angle(target_vector,fallback)

                if angle!=0:
                    axis=current_vector.cross(target_vector)
                    rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(angle,4,axis)

                    matrix[:]=rotation_matrix@parent_inverted@matrix

            shift=target_point_world-matrix@point
            matrix.col[3][0]+=shift[0]
            matrix.col[3][1]+=shift[1]
            matrix.col[3][2]+=shift[2]


def to_point_rotation(target_matrix,target_point,own_matrix,own_point,origin,min_length=0,max_length=0,
                      only_translate=False):
    own_point_world=own_matrix@own_point
    origin_world=own_matrix@origin
    target_point_world=target_matrix@target_point

    if not only_translate:

        parent_matrix=mathutils.Matrix.Identity(4)
        parent_matrix.col[3][0:3]=origin_world

        parent_inverted=parent_matrix.inverted()

        fallback=0
        current_vector=parent_inverted@own_point_world
        target_vector=parent_inverted@target_point_world

        angle=current_vector.angle(target_vector,fallback)

        if angle!=0:
            axis=current_vector.cross(target_vector)
            rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(angle,4,axis)

            own_matrix[:]=rotation_matrix@parent_inverted@own_matrix


def to_point_translation(target_matrix,target_point,own_matrix,own_point,origin,min_length=0,max_length=0,
                         only_translate=False):
    own_point_world=own_matrix@own_point
    origin_world=own_matrix@origin
    target_point_world=target_matrix@target_point

    shift=target_point_world-own_matrix@own_point
    own_matrix.col[3][0]+=shift[0]
    own_matrix.col[3][1]+=shift[1]
    own_matrix.col[3][2]+=shift[2]



def to_point_scale(matrix,point,origin,target_point_world,stretch_factor=0):

    own_point_world=matrix@point
    origin_world=matrix@origin


    parent_matrix=mathutils.Matrix.Identity(4)
    parent_matrix.col[3][0:3]=origin_world

    parent_inverted=parent_matrix.inverted()


    fallback=0
    current_vector=parent_inverted@own_point_world
    target_vector=parent_inverted@target_point_world

    angle=current_vector.angle(target_vector,fallback)

    if angle!=0:
        axis=current_vector.cross(target_vector)
        rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(angle,4,axis)

        matrix[:]=rotation_matrix@parent_inverted@matrix



    own_point_world=matrix@point
    origin_world=matrix@origin


    current_vector=own_point_world-origin_world
    target_vector=target_point_world-origin_world



    factor=1
    if current_vector.length!=0:
        factor=target_vector.length/current_vector.length
    #



    parent_matrix=mathutils.Matrix.Identity(4)

    dx=target_vector.normalized()


    for x in range(3):
        angle_vector=mathutils.Vector(parent_matrix.col[x][0:3])
        if dx.dot(angle_vector)!=0:
            break
    angle_vector=mathutils.Vector((1,1,1))

    dy=dx.cross(angle_vector).normalized()
    dz=dx.cross(dy).normalized()


    parent_matrix.col[0][0:3]=dx
    parent_matrix.col[1][0:3]=dy
    parent_matrix.col[2][0:3]=dz
    parent_matrix.col[3][0:3]=origin_world

    scaled_matrix=parent_matrix.copy()
    scaled_matrix.col[0][0:3]=dx*factor


    scaled_matrix.col[1][0:3]=dy*math.pow(factor,stretch_factor)
    scaled_matrix.col[2][0:3]=dz*math.pow(factor,stretch_factor)



    matrix[:]=scaled_matrix@parent_matrix.inverted()@matrix

    matrix[:]=compose_matrix(matrix.decompose())





def to_point(matrix,point,origin,target_point_world,only_translate=False):

    own_point_world=matrix@point
    origin_world=matrix@origin


    if not only_translate:

        parent_matrix=mathutils.Matrix.Identity(4)
        parent_matrix.col[3][0:3]=origin_world

        parent_inverted=parent_matrix.inverted()


        fallback=0
        current_vector=parent_inverted@own_point_world
        target_vector=parent_inverted@target_point_world

        angle=current_vector.angle(target_vector,fallback)

        if angle!=0:
            axis=current_vector.cross(target_vector)
            rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(angle,4,axis)

            matrix[:]=rotation_matrix@parent_inverted@matrix


    shift=target_point_world-matrix@point
    matrix.col[3][0]+=shift[0]
    matrix.col[3][1]+=shift[1]
    matrix.col[3][2]+=shift[2]

def to_point_x(matrix,point,origin,target_point_world,only_translate=False):
    own_point_world=matrix@point
    origin_world=matrix@origin

    v=own_point_world-origin_world
    tv=target_point_world-origin_world

    # target_interpolated=own_point_world+v.normalized()*(tv.length-v.length)
    target_interpolated=v.normalized()*(tv.length-v.length)

    if not only_translate:

        parent_matrix=mathutils.Matrix.Identity(4)
        parent_matrix.col[3][0:3]=origin_world

        parent_inverted=parent_matrix.inverted()

        fallback=0
        current_vector=parent_inverted@own_point_world
        target_vector=parent_inverted@target_point_world

        angle=current_vector.angle(target_vector,fallback)

        if angle!=0:
            angle*=gv.fade

            target_interpolated=own_point_world+target_interpolated*gv.fade

            axis=current_vector.cross(target_vector)

            # if axis==mathutils.Vector((0,0,0)):
            #     axis=mathutils.Vector((1,0,0))

            rotation_matrix=parent_matrix@mathutils.Matrix.Rotation(angle,4,axis)

            # print(angle,axis)

            local_target_interpolated=matrix.inverted()@target_interpolated

            matrix[:]=rotation_matrix@parent_inverted@matrix

            target_interpolated=matrix@local_target_interpolated
        else:
            target_interpolated=own_point_world+target_interpolated

    if not only_translate:
        shift=target_interpolated-matrix@point
    else:
        shift=target_point_world-matrix@point
    if tv.length>v.length or only_translate:
        matrix.col[3][0]+=shift[0]
        matrix.col[3][1]+=shift[1]
        matrix.col[3][2]+=shift[2]

def force_keyframe_insert():
    # print("FORCE KEYFRAME INSERT")
    # print(dir(bpy.context))
    gv.skip=True
    try:
        bpy.ops.anim.keyframe_insert(gv.temp_context)
        # bpy.ops.anim.compact_keyframe_insert_menu(mode='INSERT')
    except:
        pass
        print("FAILED")
    # update_animation_data()
    # read_animation_data()
    # gv.is_indirect_key_create=True
    gv.skip=False


# @persistent
# def scene_before_handler(scene):
#     pass
#     validate_structure()

def update_colors():
    for node in gv.clustered_nodes:
        node.update_color()

def reset_color(item):
    if type(item) is bpy.types.PoseBone:
        item.color.custom.normal = bpy.context.preferences.themes[0].view_3d.bone_solid
        item.color.custom.select = bpy.context.preferences.themes[0].view_3d.bone_pose
        item.color.custom.active = bpy.context.preferences.themes[0].view_3d.bone_pose_active

        item.color.palette='DEFAULT'

    elif type(item) is bpy.types.Object:
        item.color = *bpy.context.preferences.themes[0].view_3d.bone_solid,1

@persistent
def scene_before_handler(scene):
    # print(random.randint(0,100))

    if bpy.context.mode=='EDIT_ARMATURE':
        gv.time_to_force_rebuild=True

    if scene.free_ik.enable_solver and bpy.context.mode in ('POSE','OBJECT') and not gv.skip and not gv.is_rendering:
        pass
        # print()
        # print("SCENE BEFORE",random.randint(0,100))



        if gv.time_to_make_keys:
            make_keys()

        # make_keys()

        #GLOBAL FLAGS
        gv.inherit_location=bpy.context.scene.free_ik.inherit_location
        gv.inherit_rotation=bpy.context.scene.free_ik.inherit_rotation
        gv.inherit_scale=bpy.context.scene.free_ik.inherit_scale
        gv.inherit_any=gv.inherit_location or gv.inherit_rotation or gv.inherit_scale

        gv.solver_mode=bpy.context.scene.free_ik.solver_mode
        gv.stretch_mode=bpy.context.scene.free_ik.stretch_mode

        gv.scene_iterations=bpy.context.scene.free_ik.scene_iterations
        gv.frame_iterations=bpy.context.scene.free_ik.frame_iterations

        gv.use_individual_origins=(bpy.context.scene.tool_settings.transform_pivot_point=='INDIVIDUAL_ORIGINS')


        #OPERATORS

        if bpy.context.mode!=gv.last_mode:
            gv.time_to_force_rebuild=True
            gv.time_to_force_solve=True
            gv.last_mode=bpy.context.mode

        gv.operator_changed=False

        try:
            gv.last_operator.bl_idname
        except:
            gv.last_operator=None
            # gv.operator_changed=True

        # print("ACTIVE OPERATOR ",bpy.context.active_operator)
        gv.operator=None
        gv.operator=bpy.context.active_operator

        if gv.operator!=gv.last_operator:
            gv.operator_changed=True

        gv.is_pose_library=False

        gv.is_key_delete=False
        gv.is_key_create=False
        gv.is_flip_quaternion=False

        gv.is_clear_translation=False
        gv.is_clear_rotation=False
        gv.is_clear_scale=False

        gv.is_clear_pose=False
        gv.was_clear_pose=False


        if gv.operator_changed and gv.operator is not None :
            # print(gv.operator.bl_idname)

            if gv.operator.bl_idname=='POSELIB_OT_apply_pose':gv.is_pose_library=True

            if gv.operator.bl_idname in ('ACTION_OT_delete','GRAPH_OT_delete'): gv.is_key_delete=True
            if gv.operator.bl_idname=='ANIM_OT_keyframe_insert_menu': gv.is_key_create=True
            if gv.operator.bl_idname=='POSE_OT_quaternions_flip': gv.is_flip_quaternion=True

            if gv.operator.bl_idname=='POSE_OT_loc_clear': gv.is_clear_translation=True
            if gv.operator.bl_idname=='POSE_OT_rot_clear': gv.is_clear_rotation=True
            if gv.operator.bl_idname=='POSE_OT_scale_clear': gv.is_clear_scale=True
            gv.is_clear_pose=gv.is_clear_translation or gv.is_clear_rotation or gv.is_clear_scale

            if gv.is_clear_pose:
                if gv.is_clear_translation:gv.was_clear_translation=True
                if gv.is_clear_rotation:gv.was_clear_rotation=True
                if gv.is_clear_scale:gv.was_clear_scale=True
            else:
                gv.was_clear_translation=False
                gv.was_clear_rotation=False
                gv.was_clear_scale=False


        gv.last_operator=gv.operator

        # print("AFTER FRAME",gv.is_after_frame)


        # print(gv.is_clear_scale,gv.was_clear_scale)

        validate_structure()
        # update_colors()

        if gv.is_after_frame:
            read_animation_data()


        if not gv.is_modal_transform or gv.is_after_frame or gv.is_indirect_key_create:
            # print("AAA",gv.is_after_frame)
            update_animation_data()


            if gv.is_after_frame or gv.is_indirect_key_create:
                for cluster in gv.clusters:
                    cluster.animation_data_changed=False
                    gv.is_after_frame=False


        for cluster in gv.clusters:
            cluster.update_state_scene()
            if cluster.selection_changed:
                gv.was_clear_translation=False
                gv.was_clear_rotation=False
                gv.was_clear_scale=False
        gv.is_after_frame=False
        gv.is_indirect_key_create=False


        # print("IS CLEAR",gv.is_clear_pose)
        # print("    WAS LOCATION",gv.was_clear_translation)
        # print("    WAS ROTATION",gv.was_clear_rotation)
        # print("    WAS SCALE",gv.was_clear_scale)



    # for node in gv.clustered_nodes:
    #     node.transform.from_node()
    #     node.transform.location[:]=0,0,0
    #     node.transform.apply_to_limit()
    #     node.transform.apply_to_base()


@persistent
def scene_after_handler(scene):
    if scene.free_ik.enable_solver and bpy.context.mode in ('POSE','OBJECT') and not gv.skip and not gv.is_rendering:
        for cluster in gv.clusters:
            if cluster.time_to_solve_frame:
                cluster.update_state_frame()

                for node in cluster.frame.nodes:
                    node.matrix[:]=node.get_matrix()

                    node.transform.from_node()
                    node.reference_rotation=node.transform.rotation.copy()
                    node.reference_local_rotation=node.transform.local_rotation.copy()
                    node.reference_scale=node.transform.scale

                cluster.solve_frame()
                for node in cluster.nodes:
                    node.last.out_matrix[:]=node.matrix
                    node.last.out_transform.from_matrix(node.matrix)

        for node in gv.clustered_nodes:
            node.update_color()
            node.last.in_matrix[:]=node.in_matrix
            node.last.out_transform.apply_to_base()
            node.last.out_transform.apply_to_limit()





        if (gv.is_clear_pose or gv.is_pose_paste) and scene.tool_settings.use_keyframe_insert_auto and not gv.is_modal_transform:
            # print("TRY FORCE KEY")
            # print(dir(bpy.context))
            gv.temp_context=bpy.context.copy()
            bpy.app.timers.register(force_keyframe_insert)

    # update_colors()

    # for node in gv.clustered_nodes:
    #     node.transform.from_node()
    #     node.transform.location[:]=0,0,0
    #     node.transform.apply_to_limit()
    #     node.transform.apply_to_base()





@persistent
def frame_change_before_handler(scene):
    pass
    if scene.free_ik.enable_solver and not gv.skip :
        # print()
        # print("FRAME BEFORE",random.randint(0,100))
        # print(bpy.context.screen.is_animation_playing)


        gv.frame_iterations=bpy.context.scene.free_ik.frame_iterations

        for node in gv.clustered_nodes:
            pass
            node.default_transform.apply_to_base()
            if gv.is_rendering:
                node.source.id_data.update_tag(refresh={'TIME'})



    # print("FRAME BEFORE",random.randint(0,100))




def source_from_graph(graph,item):
    if type(item)==Node:
        if item.is_bone:
            return graph.objects[item.source.id_data.name].pose.bones[item.source.name]
        else:
            return graph.objects[item.source.name]
    else:
        return graph.objects[item.source.name]




@persistent
def frame_change_after_handler(scene,graph):
    pass
    if scene.free_ik.enable_solver and not gv.skip and not gv.is_rendering:

        # print()
        # print("FRAME AFTER")



        gv.is_playback=False
        if bpy.context.screen is not None:
            gv.is_playback=bpy.context.screen.is_animation_playing

        gv.playback_stopped=False
        if not gv.is_playback and gv.was_playback:
            gv.playback_stopped=True



        gv.was_playback=gv.is_playback

        # print(gv.is_playback)
        # print(gv.playback_stopped)

        validate_frame()

        for cluster in gv.clusters:
            cluster.update_state_frame()


            cluster.time_to_solve_frame=False
            cluster.time_to_apply=True
            for node in cluster.nodes:

                node.transform.from_node()
                node.reference_rotation=node.transform.rotation.copy()
                node.reference_local_rotation=node.transform.local_rotation.copy()
                node.reference_scale=node.transform.scale

                if not node.transform.simple_compare(node.last.out_transform):cluster.time_to_solve_frame=True
                if not node.transform.simple_compare(node.last.in_transform) or not gv.is_after_frame: cluster.time_to_apply=False
                node.last.in_transform.from_other(node.transform)
            # print("TIME TO SOLVE",cluster.time_to_solve_frame)
            # print("TIME TO APPLY",cluster.time_to_apply)



            if cluster.time_to_solve_frame:

                if not cluster.time_to_apply:

                    for node in cluster.frame.nodes:
                        node.matrix[:]=node.get_matrix()


                    cluster.solve_frame()

                    for node in cluster.nodes:
                        node.last.out_matrix[:]=node.matrix
                        node.last.out_transform.from_matrix(node.matrix)
                        # node.last.out_transform.from_other(node.transform)

                for node in cluster.nodes:
                    node.last.out_matrix[:]=node.matrix
                    if not gv.is_playback or (gv.is_modal_transform and scene.tool_settings.use_keyframe_insert_auto) or True:
                        node.last.out_transform.apply_to_base()

                    node.last.out_transform.apply_to_limit()

                    if cluster.pinning_changed:
                        node.update_color()





        gv.is_indirect_key_create=False
        gv.is_after_frame=True

        # print("PLAYBACK",gv.is_playback)



    if gv.is_rendering:

        for link in gv.links:
            link.update_state_from_other(source_from_graph(graph,link))


        make_clusters()
        for cluster in gv.clusters:
            for node in cluster.nodes:
                node.temp_source=source_from_graph(graph,node)
                node.update_state_from_other(node.temp_source)

            cluster.update_frame_level()
            cluster.make_frame_solve_data()
            for node in cluster.frame.nodes:
                node.transform.from_other_source(node.temp_source)
                node.reference_rotation=node.transform.rotation.copy()
                node.reference_local_rotation=node.transform.local_rotation.copy()
                node.reference_scale=node.transform.scale

                node.matrix[:]=node.get_matrix_from_other(node.temp_source)
                # node.matrix[:]=mathutils.Matrix.Identity(4)
            cluster.solve_frame()
            for node in cluster.frame.nodes:
                # node.matrix[:]=mathutils.Matrix.Identity(4)
                node.last.out_transform.from_matrix(node.matrix)
                node.last.out_transform.apply_to_limit()
                node.last.out_transform.apply_to_base()

                node.update_color()

        gv.is_indirect_key_create=False
        gv.is_after_frame=True

    # update_colors()

    # print( bpy.data.objects["Armature"].pose.bones["Bone.009.L"].location)
    # print(graph.objects["Armature"].pose.bones["Bone.009.L"].location)


    # graph.objects["Armature"].pose.bones["Bone.009.L"].location=1,1,1
    # graph.objects["Armature"].pose.bones["Bone.009.L"].free_ik.limit_location=1,1,1
    #
    #
    #
    # bpy.data.objects["Armature"].pose.bones["Bone.009.L"].location=10,1,1
    # bpy.data.objects["Armature"].pose.bones["Bone.009.L"].free_ik.limit_location=10,1,1


    # print()
    # print(id(bpy.data.objects["Armature"]),id(graph.objects["Armature"]))
    # for node in gv.clustered_nodes:
    #     node.source.location=100,100,100




    # graph.update()



@persistent
def validation_handler(scene):
    # print("VALIDATION")
    gv.time_to_force_rebuild=True
    reset_structure()
    validate_structure()
    for cluster in gv.clusters:
        cluster.update_state_scene()
    read_animation_data()


# class FreeIKParentingMenu(bpy.types.Operator):
#     """Connect selected rigid bodies with rigid body constraints"""
#     bl_idname = "free_ik.parenting_menu"
#     bl_label = "-Parenting menu"
#     # bl_options = {'REGISTER', 'UNDO','PRESET'}
#     bl_options=set()
#
#
#     @classmethod
#     def poll(self, context):
#         return True
#
#     def execute(self, context):
#         pass#print("TEST")
#         return {'FINISHED'}
#     def invoke(self,context,event):
#         pass#print("INVOKE")
#         return context.window_manager.invoke_props_dialog(self)
#
#     def draw(self, context):
#         layout = self.layout
#
#         layout.operator(SetPoseParent.bl_idname, icon='MESH_CAPSULE')
#         layout.operator(ClearPoseParent.bl_idname,icon='MESH_CAPSULE')
#
#         layout.prop(context.scene.free_ik,"inherit_location")
#         layout.prop(context.scene.free_ik,"inherit_rotation")
#         layout.prop(context.scene.free_ik,"inherit_scale")


class KeyMapOperator(bpy.types.Operator):
    bl_idname = "preferences.free_ik_keymap_operator"
    bl_label="Keymap operator"

    mode:bpy.props.EnumProperty(name="Mode",
                                      items=[
                                          ('MAKE',"","",'NONE',0),
                                          ('CLEAR',"","",'NONE',1),
                                          ('RESTORE',"","",'NONE',2),
                                          ('RESOLVE',"","",'NONE',3)
                                      ]
                                      )
    target_idname:bpy.props.StringProperty()
    # target_keymap_name:bpy.props.StringProperty()
    conflict_keymap_names: bpy.props.StringProperty()
    id_to_resolve: bpy.props.IntProperty()

    def execute(self, context):

        if self.mode=='MAKE':
            context.keymap_items.new(idname=self.target_idname,type='NONE',value='PRESS',head=True)

        if self.mode=='CLEAR':
            context.keymap_items.remove(context.keymap_items.from_id(self.id_to_resolve))
        if self.mode=='RESTORE':
            keymap_item=context.keymap_items.from_id(self.id_to_resolve)
            # print(dir(keymap_item))
            # print(keymap_item.propvalue,keymap_item.map_type)
            keymap_item.map_type='KEYBOARD'
            keymap_item.value='PRESS'
            keymap_item.type='NONE'
            keymap_item.key_modifier='NONE'
            keymap_item.any=False
            keymap_item.ctrl=False
            keymap_item.oskey=False
            keymap_item.alt=False
            keymap_item.shift=False

        if self.mode=='RESOLVE':
            keymap_holder=bpy.context.window_manager.keyconfigs.user.keymaps
            conflict_keymaps=[keymap_holder[name] for name in self.conflict_keymap_names.split(',')]

            active_item=context.keymap.keymap_items.from_id(self.id_to_resolve)
            for conflict_keymap in conflict_keymaps:
                # print(conflict_keymap)
                for keymap_item in conflict_keymap.keymap_items:
                    if keymap_item.active and keymap_item.compare(active_item) and keymap_item!=active_item:
                        keymap_item.active=False








        return {'FINISHED'}


class Preferences(bpy.types.AddonPreferences):

    bl_idname = __name__


    def check(self,context):
        return True

    def draw_keymap_item(self,layout,target_idname,target_keymap_name,target_label,conflict_keymap_names):
        # print()
        # print(target_label,target_keymap_name)

        keymap_holder=bpy.context.window_manager.keyconfigs.user.keymaps
        target_keymap=keymap_holder[target_keymap_name]
        conflict_keymaps=[keymap_holder[name] for name in conflict_keymap_names]
        for conflict_keymap in conflict_keymaps:
            conflict_keymap.keymap_items.update()

        target_item=None

        for keymap_item in target_keymap.keymap_items:
            if keymap_item.idname==target_idname:
                target_item=keymap_item
                break

        conflict_items=[]
        # print(target_item)
        if target_item is not None:
            for conflict_keymap in conflict_keymaps:
                for keymap_item in conflict_keymap.keymap_items:

                    # if keymap_item.compare(target_item):print(keymap_item)

                    if keymap_item.active and keymap_item.compare(target_item) and keymap_item!=target_item:
                        if keymap_item.type!='NONE' or keymap_item.key_modifier!='NONE' or any((keymap_item.any,keymap_item.ctrl,keymap_item.oskey,keymap_item.alt,keymap_item.shift)):
                            # print(keymap_item)
                            conflict_items.append(keymap_item)


        row=layout.row()
        row.label(text=target_label)
        if target_item is None:
            row.context_pointer_set("keymap_items",target_keymap.keymap_items)
            operator=row.operator(KeyMapOperator.bl_idname,text="Create mapping")
            operator.mode='MAKE'
            operator.target_idname=target_idname

        else:
            row.prop(target_item,"value")
            row.prop(target_item,"type",full_event=True,text="")

            row.context_pointer_set("keymap_items",target_keymap.keymap_items)
            operator=row.operator(KeyMapOperator.bl_idname,text="",icon='BACK')
            operator.mode='RESTORE'
            operator.id_to_resolve=target_item.id

            row.context_pointer_set("keymap_items",target_keymap.keymap_items)
            operator=row.operator(KeyMapOperator.bl_idname,text="",icon='X')
            operator.mode='CLEAR'
            operator.id_to_resolve=target_item.id

            if len(conflict_items)!=0:
                layout.context_pointer_set("keymap",target_keymap)
                operator=layout.operator(KeyMapOperator.bl_idname,text=f"Disable {len(conflict_items)} conflicting mappings ")
                operator.mode='RESOLVE'
                operator.id_to_resolve=target_item.id
                operator.conflict_keymap_names=",".join(conflict_keymap_names)

        layout.separator()

    def draw(self, context):
        layout = self.layout
        # layout.separator()

        target_keymap_name='3D View'
        conflict_keymap_names=(target_keymap_name,'Object Mode','Pose')

        self.draw_keymap_item(layout,target_idname=FreeIKPieMenuStarter.bl_idname,target_keymap_name='3D View',target_label="Pie menu",conflict_keymap_names=conflict_keymap_names)
        self.draw_keymap_item(layout,target_idname=FreeIKChangeModeStarter.bl_idname,target_keymap_name='3D View',target_label="Change mode",conflict_keymap_names=conflict_keymap_names)







class FREEIK_PT_FreeIKParentingMenu(bpy.types.Panel):
    """I am help string"""
    bl_label="Parent settings"
    bl_space_type='VIEW_3D'
    bl_region_type='WINDOW'

    # bl_owner_id="FreeIKPieMenu"
    # bl_parent_id="FreeIKPieMenu"

    def draw(self,context):
        layout=self.layout

        layout.prop(context.scene.free_ik,"inherit_location")
        layout.prop(context.scene.free_ik,"inherit_rotation")
        layout.prop(context.scene.free_ik,"inherit_scale")

    # def draw_header(self, context):
    #     layout = self.layout
    #
    #     layout.prop(context.scene.free_ik,"inherit_location")
    #     layout.prop(context.scene.free_ik,"inherit_rotation")
    #     layout.prop(context.scene.free_ik,"inherit_scale")
    #


#
#
# class FreeIKMenu(bpy.types.Menu):
#     """I am help string"""
#     bl_label = "FreeIK  menu"
#
#     def draw(self, context):
#         layout = self.layout
#         pie = layout.menu_pie()
#
#
#         layout.operator(MakeLinks.bl_idname, icon='MESH_CAPSULE')
#         layout.operator(ClearLinks.bl_idname, icon='MESH_CAPSULE')
#
#         layout.operator(SetPinState.bl_idname,text="Pin selected",icon='MESH_CAPSULE').pin_state=True
#         layout.operator(SetPinState.bl_idname,text="Unpin selected",icon='MESH_CAPSULE').pin_state=False
#
#         layout.operator(SetPoseParent.bl_idname, icon='MESH_CAPSULE')
#         layout.operator(ClearPoseParent.bl_idname,icon='MESH_CAPSULE')
#
#
#         # layout.prop(context.scene.free_ik,"inherit_location")

# class FreeIKPanel(bpy.types.Panel):
#     bl_idname = "OBJECT_PT_free_ik_panel"
#     bl_label = "FreeIK panel"
#     bl_space_type = 'PROPERTIES'
#     bl_region_type = 'WINDOW'
#     # bl_context = "object"
#     bl_options={'HIDE_HEADER'}
#
#     @classmethod
#     def poll(self, context):
#         return True
#
#
#
#     def draw(self, context):
#         layout = self.layout
#         pie = layout.menu_pie()
#
#         column=pie.column()
#         column.operator(MakeLinks.bl_idname, icon='MESH_CAPSULE')
#         column.operator(ClearLinks.bl_idname, icon='MESH_CAPSULE')
#
#         column=pie.column()
#         column.scale_x=1.5
#         column.scale_y=1.5
#         column.operator(SetPinState.bl_idname,text="Pin", icon='MESH_CAPSULE').pin_state=True
#         column.operator(SetPinState.bl_idname,text="Unpin", icon='MESH_CAPSULE').pin_state=False
#
#
#
#         column=pie.column()
#         column.operator(SetPoseParent.bl_idname, icon='MESH_CAPSULE')
#         column.operator(ClearPoseParent.bl_idname, icon='MESH_CAPSULE')
#         column.prop(context.scene.free_ik,"inherit_location")
#         column.prop(context.scene.free_ik,"inherit_rotation")
#         column.prop(context.scene.free_ik,"inherit_scale")


class FREEIK_MT_ChangeMode(bpy.types.Menu):
    bl_label="Change mode"

    def draw(self,context):
        layout=self.layout
        pie=layout.menu_pie()

        column=pie.column(align=True)
        column.scale_x=1.5
        column.scale_y=1.5
        depress= context.scene.free_ik.solver_mode==gv.smooth
        column.operator(SetSolverMode.bl_idname,text="Smooth",icon='OUTLINER_OB_CURVE',depress=depress).mode='SMOOTH'



        column=pie.column(align=True)
        column.scale_x=1.5
        column.scale_y=1.5
        depress= context.scene.free_ik.solver_mode==gv.rope
        column.operator(SetSolverMode.bl_idname,text="Rope",icon='GP_SELECT_STROKES',depress=depress).mode='ROPE'

        column=pie.column(align=True)
        column.scale_x=1.5
        column.scale_y=1.5
        depress=context.scene.free_ik.solver_mode==gv.stretch and context.scene.free_ik.stretch_mode==gv.stretch_both
        column.operator(SetSolverMode.bl_idname,text="Stretch",icon='FULLSCREEN_ENTER',depress=depress).mode='STRETCH_BOTH'

        if context.mode=='POSE':
            depress=context.scene.free_ik.solver_mode==gv.stretch and context.scene.free_ik.stretch_mode==gv.stretch_head
            column.operator(SetSolverMode.bl_idname,text="Head",icon='NONE',depress=depress).mode='STRETCH_HEAD'
            depress=context.scene.free_ik.solver_mode==gv.stretch and context.scene.free_ik.stretch_mode==gv.stretch_tail
            column.operator(SetSolverMode.bl_idname,text="Tail",icon='NONE',depress=depress).mode='STRETCH_TAIL'



class FreeIKChangeModeStarter(bpy.types.Operator):
    bl_idname="free_ik.change_mode_start"
    bl_label="Change mode"

    @classmethod
    def poll(self,context):
        return context.mode in ('OBJECT','POSE')

    def invoke(self,context,event):
        bpy.ops.wm.call_menu_pie(name="FREEIK_MT_ChangeMode")
        return {'FINISHED'}


class FREEIK_MT_FreeIKPieMenu(bpy.types.Menu):
    """I am help string"""
    bl_label="FreeIK pie menu"

    def draw(self,context):
        layout=self.layout
        pie=layout.menu_pie()

        column=pie.column(align=True)
        column.scale_x=1.5
        column.scale_y=1.5
        column.operator(MakeLinks.bl_idname,text="Make links",icon='POSE_HLT')

        row=column.row(align=True)
        split=row.split(align=True,factor=0.5)

        split.operator(Bake.bl_idname,text="Bake",icon='ACTION')
        split.operator(SetRigState.bl_idname,text="",icon='OUTLINER_OB_LIGHT').rig_state=True
        split.operator(SetRigState.bl_idname,text="",icon='LIGHT').rig_state=False

        column.operator(ClearLinks.bl_idname,text="Clear links",icon='PANEL_CLOSE')

        column=pie.column(align=True)
        column.scale_x=1.5
        column.scale_y=1.5
        column.operator(SetParent.bl_idname,text="Set pose parent",icon='MESH_CAPSULE').mode='POSE'
        column.operator(ClearParent.bl_idname,text="Clear pose parent",icon='PANEL_CLOSE').mode='POSE'
        column.popover("FREEIK_PT_FreeIKParentingMenu")

        row=pie.row(align=True)
        row.scale_x=row.scale_y=1.5

        column=row.column(align=True)
        column.scale_x=1.0
        column.operator(SetLinkState.bl_idname,text="Enable link",icon='LINKED').link_state=True
        column.operator(SetLinkState.bl_idname,text="Disable link",icon='UNLINKED').link_state=False

        column=row.column(align=True)
        column.scale_y=2
        column.scale_x=1
        row=column.row(align=True)
        operator=row.operator(Keyframer.bl_idname,text="",text_ctxt="Isert keyframe",icon='KEY_HLT')
        operator.mode='INSERT'
        operator.target='IS_ENABLED'

        operator=row.operator(Keyframer.bl_idname,text="",text_ctxt="Delete keyframe",icon='KEY_DEHLT')
        operator.mode='DELETE'
        operator.target='IS_ENABLED'

        operator=row.operator(Keyframer.bl_idname,text="",text_ctxt="Clear keyframes",icon='X')
        operator.mode='CLEAR'
        operator.target='IS_ENABLED'

        row=pie.row(align=True)
        row.scale_x=row.scale_y=1.5

        column=row.column(align=True)
        column.scale_x=1.0
        column.operator(SetPinState.bl_idname,text="Pin",icon='PINNED').pin_state=True
        column.operator(SetPinState.bl_idname,text="Unpin",icon='UNPINNED').pin_state=False

        column=row.column(align=True)
        column.scale_y=2
        column.scale_x=1
        row=column.row(align=True)
        operator=row.operator(Keyframer.bl_idname,text="",text_ctxt="Isert keyframe",icon='KEY_HLT')
        operator.mode='INSERT'
        operator.target='IS_PINNED'

        operator=row.operator(Keyframer.bl_idname,text="",text_ctxt="Delete keyframe",icon='KEY_DEHLT')
        operator.mode='DELETE'
        operator.target='IS_PINNED'

        operator=row.operator(Keyframer.bl_idname,text="",text_ctxt="Clear keyframes",icon='X')
        operator.mode='CLEAR'
        operator.target='IS_PINNED'


class FreeIKPieMenuStarter(bpy.types.Operator):
    bl_idname="free_ik.pie_menu_start"
    bl_label="FreeIK tools pie menu"

    @classmethod
    def poll(self,context):
        return context.mode in ('OBJECT','POSE')

    def invoke(self,context,event):
        bpy.ops.wm.call_menu_pie(name="FREEIK_MT_FreeIKPieMenu")
        return {'FINISHED'}


class Keyframer(bpy.types.Operator):
    """Insert or delete keyframes"""
    bl_idname="free_ik.keyframer"
    bl_label="Keyframer"
    bl_options={'REGISTER','UNDO'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('INSERT',"Insert","Insert",'NONE',0),
                                     ('DELETE',"Delete","Delete",'NONE',1),
                                     ('CLEAR',"Clear","Clear",'NONE',2),
                                 ]
                                 )
    target: bpy.props.EnumProperty(name="Target",
                                   items=[
                                       ('IS_PINNED',"Is pinned","Is pinned",'NONE',0),
                                       ('IS_ENABLED',"Is enabled","Is enabled",'NONE',1),
                                   ]
                                   )

    @classmethod
    def poll(self,context):
        return True

    def execute(self,context):
        pass  #print("EXECUTE",self.mode,self.target)



        if context.mode=='POSE':

            if self.target == 'IS_ENABLED':
                selected_items = []
                selected_pose_bones = set(context.selected_pose_bones)

                for link in gv.links:
                    if link.node_a.source in selected_pose_bones and link.node_b.source in selected_pose_bones:
                        selected_items.append(link.source)

            if self.target == 'IS_PINNED':
                selected_items = [item for item in context.selected_pose_bones if item in gv.nodes_dictionary]

        if context.mode=='OBJECT':
            selected_items=[item for item in context.selected_objects if item in gv.links_dictionary or item in gv.nodes_dictionary]

        pass  #print(selected_items)

        for item in selected_items:
            data_path=None
            if type(item)==bpy.types.PoseBone:
                if self.target=='IS_PINNED': data_path="free_ik_is_pinned"

                base_path='pose.bones["{}"].'.format(item.name)
                fcurve_holder=item.id_data

            if type(item)==bpy.types.Object:
                if self.target=='IS_PINNED' and item in gv.nodes_dictionary: data_path="free_ik_is_pinned"
                if self.target=='IS_ENABLED' and item in gv.links_dictionary: data_path="free_ik.is_enabled"

                base_path=""
                fcurve_holder=item
            pass  #print(data_path)

            if data_path is not None:
                if self.mode=='INSERT':
                    item.keyframe_insert(data_path)
                if self.mode=='DELETE':
                    if fcurve_holder.animation_data is not None:
                        if fcurve_holder.animation_data.action is not None:
                            item.keyframe_delete(data_path)
                if self.mode=='CLEAR':
                    if fcurve_holder.animation_data is not None:
                        if fcurve_holder.animation_data.action is not None:
                            to_remove=fcurve_holder.animation_data.action.fcurves.find(base_path+data_path)
                            if to_remove is not None:
                                fcurve_holder.animation_data.action.fcurves.remove(to_remove)
                                fcurve_holder.animation_data.action.fcurves.update()

        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)

        return {'FINISHED'}


class Bake(bpy.types.Operator):
    """Bake"""
    bl_idname="free_ik.bake"
    bl_label="Bake"
    bl_options={'REGISTER','UNDO'}

    use_selected_bones_only: bpy.props.BoolProperty(name="Use selected bones only",default=False)
    use_custom_range: bpy.props.BoolProperty(name="Use custom range",default=False)
    start_frame: bpy.props.IntProperty(name="Start frame",description="Start frame for baking",default=1,min=0)
    end_frame: bpy.props.IntProperty(name="End frame",description="End frame for baking",default=250,min=1)

    use_parents: bpy.props.BoolProperty(name="Use hierarchy",default=False)


    @classmethod
    def poll(self,context):
        return context.mode in ('OBJECT','POSE')

    def execute(self,context):
        pass  #print("EXECUTE")

        work_nodes=[]
        work_armatures=set()

        if context.mode=='OBJECT':
            for selected_object in context.selected_objects:
                if type(selected_object.data)==bpy.types.Armature:
                    for pose_bone in selected_object.pose.bones:
                        if not pose_bone.bone.hide:
                            if pose_bone.bone.select or not self.use_selected_bones_only:
                                # if any([bl and al for bl,al in zip(pose_bone.bone.layers,selected_object.data.layers)]):
                                if len(pose_bone.bone.collections) == 0 or any(collection.is_visible for collection in pose_bone.bone.collections):
                                    if pose_bone in gv.nodes_dictionary:
                                        work_nodes.append(gv.nodes_dictionary[pose_bone])
                                        work_armatures.add(pose_bone.id_data)
                else:
                    if selected_object in gv.nodes_dictionary:
                        work_nodes.append(gv.nodes_dictionary[selected_object])

        if context.mode=='POSE':
            if self.use_selected_bones_only:
                pose_bones=context.selected_pose_bones
            else:
                pose_bones=context.visible_pose_bones
            for pose_bone in pose_bones:
                if pose_bone in gv.nodes_dictionary:
                    work_nodes.append(gv.nodes_dictionary[pose_bone])
                    work_armatures.add(pose_bone.id_data)

        work_nodes.sort(key=lambda v:v.frame_level)

        action_holders=set()
        for node in work_nodes:
            action_holders.add(node.source.id_data)

        parented_bone_nodes=[node for node in work_nodes if node.is_bone and node.frame_parent is not None]
        parented_object_nodes=[node for node in work_nodes if not node.is_bone and node.frame_parent is not None]
        work_sources=[node.source for node in work_nodes]
        work_parents=[]
        for node in work_nodes:
            work_parent=None
            if node.is_bone:
                if node.frame_parent is not None:
                    if node.source_armature==node.frame_parent.source_armature:
                        work_parent=node.frame_parent.source

            work_parents.append(work_parent)

        before_matrices=[]

        for node in work_nodes:
            if node.is_bone:
                matrix=node.source_armature.matrix_basis@node.source.bone.matrix_local@node.source.matrix_basis
                before_matrices.append(matrix)
                node.matrix[:]=matrix
            else:
                before_matrices.append(node.source.matrix_world.copy())

        if self.use_custom_range:
            custom_range=range(self.start_frame,self.end_frame)
        else:
            custom_range=None
        trajectories=get_trajectories(set([item for item in itertools.chain(work_sources,work_parents) if item is not None]),custom_range)

        make_new_action(action_holders)
        pass  #print(len(work_sources),len(work_parents),len(trajectories))
        apply_trajectories(work_sources,trajectories,work_parents,apply_local=self.use_parents)
        # context.scene.frame_set(context.scene.frame_current)

        for matrix,node in zip(before_matrices,work_nodes):
            if node.is_bone:
                if node.frame_parent is not None:
                    node.source.matrix_basis=(node.frame_parent.matrix@(
                                node.frame_parent.source.bone.matrix_local.inverted()@node.source.bone.matrix_local)).inverted()@matrix
                else:
                    node.source.matrix_basis=(node.source_armature.matrix_basis@node.source.bone.matrix_local).inverted()@matrix
            else:
                node.source.matrix_world=matrix

        return {'FINISHED'}

    def invoke(self,context,event):
        # context.scene.update()
        return context.window_manager.invoke_props_dialog(self)

    def check(self,context):
        return True

    def draw(self,context):
        pass  #print("DRAW")
        layout=self.layout
        layout.alignment='LEFT'
        layout.prop(self,"use_selected_bones_only")
        layout.prop(self,"use_parents")
        layout.prop(self,"use_custom_range")
        if self.use_custom_range:
            layout.prop(self,"start_frame")
            layout.prop(self,"end_frame")



class ClearLinks(bpy.types.Operator):
    """Clear links"""
    bl_idname="free_ik.clear_links"
    bl_label="Clear links"
    bl_options={'REGISTER','UNDO'}

    def clear_drivers(self,item):
        if type(item)==bpy.types.PoseBone:
            base_path=f'pose.bones["{item.name}"].constraints'
        else:
            base_path=f'constraints'

        limit_names=(gv.limit_location_name,gv.limit_rotation_name,gv.limit_scale_name)
        property_names=("min","max")
        axis_names=("x","y","z")

        for limit_name in limit_names:
            for property_name in property_names:
                for axis_name in axis_names:
                    pass  #print(base_path+f'["{limit_name}"].{property_name}_{axis_name}')
                    out=item.id_data.driver_remove(base_path+f'["{limit_name}"].{property_name}_{axis_name}')
                    pass  #print(out)

    use_selected_bones_only: bpy.props.BoolProperty(name="Use selected bones only",default=False)

    adapt_animation: bpy.props.BoolProperty(name="Adapt animation",default=False)

    make_parents: bpy.props.BoolProperty(name="Make hierarchy",default=True)

    connected_bones: bpy.props.BoolProperty(name="Connected bones",default=False)

    use_custom_range: bpy.props.BoolProperty(name="Use custom range",default=False)
    start_frame: bpy.props.IntProperty(name="Start frame",description="Start frame for baking",default=1,min=0)
    end_frame: bpy.props.IntProperty(name="End frame",description="End frame for baking",default=250,min=1)

    @classmethod
    def poll(self,context):
        return context.mode in ('OBJECT','POSE')

    def execute(self,context):
        pass  #print("EXECUTE")

        work_nodes=[]
        work_armatures=set()

        if context.mode=='OBJECT':
            for selected_object in context.selected_objects:
                if type(selected_object.data)==bpy.types.Armature:
                    for pose_bone in selected_object.pose.bones:
                        if not pose_bone.bone.hide:
                            if pose_bone.bone.select or not self.use_selected_bones_only:
                                # if any([bl and al for bl,al in zip(pose_bone.bone.layers,selected_object.data.layers)]):
                                if len(pose_bone.bone.collections) == 0 or any(collection.is_visible for collection in pose_bone.bone.collections):
                                    if pose_bone in gv.nodes_dictionary:
                                        work_nodes.append(gv.nodes_dictionary[pose_bone])
                                        work_armatures.add(pose_bone.id_data)
                else:
                    if selected_object in gv.nodes_dictionary:
                        work_nodes.append(gv.nodes_dictionary[selected_object])

        if context.mode=='POSE':
            if self.use_selected_bones_only:
                pose_bones=context.selected_pose_bones
            else:
                pose_bones=context.visible_pose_bones
            for pose_bone in pose_bones:
                if pose_bone in gv.nodes_dictionary:
                    work_nodes.append(gv.nodes_dictionary[pose_bone])
                    work_armatures.add(pose_bone.id_data)

        work_nodes.sort(key=lambda v:v.frame_level)

        action_holders=set()
        for node in work_nodes:
            if node.is_bone:
                action_holders.add(node.source_armature)
            else:
                action_holders.add(node.source)

        parented_bone_nodes=[node for node in work_nodes if node.is_bone and node.frame_parent is not None]
        parented_object_nodes=[node for node in work_nodes if not node.is_bone and node.frame_parent is not None]
        work_sources=[node.source for node in work_nodes]
        work_parents=[]
        for node in work_nodes:
            work_parent=None
            if node.is_bone:
                if node.frame_parent is not None:
                    if node.source_armature==node.frame_parent.source_armature:
                        work_parent=node.frame_parent.source

            work_parents.append(work_parent)

        before_matrices=[]

        for node in work_nodes:
            if node.is_bone:
                # before_matrices.append(node.source_armature.convert_space(pose_bone=node.source,matrix=node.source.matrix,from_space='POSE',to_space='WORLD'))
                matrix=node.source_armature.matrix_basis@node.source.bone.matrix_local@node.source.matrix_basis
                before_matrices.append(matrix)
                node.matrix[:]=matrix
            else:
                before_matrices.append(node.source.matrix_world.copy())

        if self.adapt_animation:
            if self.use_custom_range:
                custom_range=range(self.start_frame,self.end_frame)
            else:
                custom_range=None
            trajectories=get_trajectories(
                set([item for item in itertools.chain(work_sources,work_parents) if item is not None]),custom_range)

        if self.make_parents:
            if len(parented_bone_nodes)!=0:
                last_selected=context.selected_objects.copy()
                last_active=context.object
                last_mode=context.mode

                for item in bpy.data.objects:
                    item.select_set(False)
                for item in work_armatures:
                    item.select_set(True)
                context.view_layer.objects.active=next(iter(work_armatures))

                bpy.ops.object.mode_set(mode='EDIT')

                for node in parented_bone_nodes:

                    if node.frame_parent.source_armature==node.source_armature:
                        node.source_armature.data.edit_bones[node.source.name].parent=node.source_armature.data.edit_bones[node.frame_parent.source.name]
                        # print(node,node.source.free_ik_was_connected)
                        if node.source.free_ik_was_connected:
                            node.source_armature.data.edit_bones[node.source.name].use_connect=True
                        else:
                            node.source_armature.data.edit_bones[node.source.name].use_connect=False

                        # if self.connected_bones:
                        #     node.source_armature.data.edit_bones[node.source.name].use_connect=True
                        # else:
                        #     node.source_armature.data.edit_bones[node.source.name].use_connect=False

                bpy.ops.object.mode_set(mode=last_mode)

                for item in bpy.data.objects:
                    item.select_set(False)
                for item in last_selected:
                    item.select_set(True)
                context.view_layer.objects.active=last_active

        if self.adapt_animation:
            # make_new_action(action_holders)
            pass  #print(len(work_sources),len(work_parents),len(trajectories))
            apply_trajectories(work_sources,trajectories,work_parents,apply_local=self.make_parents)
            # context.scene.frame_set(context.scene.frame_current)


        # context.view_layer.update()
        for matrix,node in zip(before_matrices,work_nodes):
            node.matrix[:]=matrix



        for matrix,node in zip(before_matrices,work_nodes):
            if node.is_bone:
                if node.frame_parent is not None:

                    node.source.matrix_basis=(node.frame_parent.matrix@(node.frame_parent.source.bone.matrix_local.inverted()@node.source.bone.matrix_local)).inverted()@matrix
                else:
                    node.source.matrix_basis=(node.source_armature.matrix_basis@node.source.bone.matrix_local).inverted()@matrix
            else:
                node.source.matrix_world=matrix



        # for matrix,node in zip(before_matrices,work_nodes):
        #     if node.is_bone:
        #         node.source.matrix_basis=node.source.id_data.convert_space(pose_bone=node.source,matrix=matrix,from_space='WORLD',to_space='LOCAL')
        #     else:
        #         node.source.matrix_world=matrix
        #

        for source in work_sources:
            reset_color(source)

        for source in work_sources:
            self.clear_drivers(source)

        const_names=(
        gv.limit_location_name,gv.limit_rotation_name,gv.limit_scale_name,gv.pose_parent_name,gv.frame_parent_name)
        for source in work_sources:
            for const_name in const_names:
                if const_name in source.constraints:
                    source.constraints.remove(source.constraints[const_name])

        links_to_delete=set()
        for node in work_nodes:
            for link in node.links:
                links_to_delete.add(link.source)

        for link in links_to_delete:
            bpy.data.objects.remove(link)

        names=("free_ik","free_ik_is_pinned","free_ik_local_quaternion","free_ik_local_euler","free_ik_local_axis_angle")
        for node in work_nodes:
            for name in names:
                # rna_prop_ui.rna_idprop_ui_prop_update(node.source,name)
                if name in node.source:
                    del node.source[name]
                # rna_prop_ui.rna_idprop_ui_prop_clear(node.source,name)

        gv.time_to_force_rebuild=True
        validate_structure()




        # print("CLEAR FINISHED")

        return {'FINISHED'}

    def invoke(self,context,event):
        # context.scene.update()
        return context.window_manager.invoke_props_dialog(self)

    def check(self,context):
        return True

    def draw(self,context):
        pass  #print("DRAW")
        layout=self.layout
        layout.alignment='LEFT'

        layout.prop(self,"use_selected_bones_only")
        layout.prop(self,"make_parents")
        # layout.prop(self,"connected_bones")

        layout.prop(self,"adapt_animation")
        if self.adapt_animation:
            layout.prop(self,"use_custom_range")
            if self.use_custom_range:
                layout.prop(self,"start_frame")
                layout.prop(self,"end_frame")


class MakeLinks(bpy.types.Operator):
    """Make links"""
    bl_idname="free_ik.make_links"
    bl_label="Make links"
    # bl_options = {'REGISTER', 'UNDO','USE_EVAL_DATA'}
    bl_options={'REGISTER','UNDO'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('ARMATURE',"Armature","Create links from armature",'NONE',0),
                                     ('CURSOR',"Two objects","Link two objects",'NONE',1),
                                 ]
                                 )
    use_selected_bones_only: bpy.props.BoolProperty(name="Use selected bones only",default=False)

    adapt_animation: bpy.props.BoolProperty(name="Adapt animation",default=False)

    use_custom_range: bpy.props.BoolProperty(name="Use custom range",default=False)
    start_frame: bpy.props.IntProperty(name="Start frame",description="Start frame for baking",default=1,min=0)
    end_frame: bpy.props.IntProperty(name="End frame",description="End frame for baking",default=250,min=1)


    @classmethod
    def poll(self,context):
        return context.mode in ('OBJECT','POSE')

    def execute(self,context):
        pass  #print("EXECUTE")

        return {'FINISHED'}

    def invoke(self,context,event):
        # context.scene.update()
        return context.window_manager.invoke_props_dialog(self)

    def check(self,context):
        return True

    def draw(self,context):

        layout=self.layout
        layout.prop(self,"mode")
        if self.mode=='ARMATURE':
            layout.prop(self,"use_selected_bones_only")
            layout.prop(self,"adapt_animation")
            if self.adapt_animation:
                layout.prop(self,"use_custom_range")
                if self.use_custom_range:
                    layout.prop(self,"start_frame")
                    layout.prop(self,"end_frame")


class SetSolverMode(bpy.types.Operator):
    """Set mode"""
    bl_idname="free_ik.set_solver_mode"
    bl_label="Set mode"
    bl_options=set()

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('SMOOTH',"","",'NONE',0),
                                     ('ROPE',"","",'NONE',1),
                                     ('STRETCH_BOTH',"","",'NONE',2),
                                     ('STRETCH_HEAD',"","",'NONE',3),
                                     ('STRETCH_TAIL',"","",'NONE',4),

                                 ]
                                 )

    @classmethod
    def poll(self,context):
        return True

    def execute(self,context):
        pass  #print("EXECUTE")

        if self.mode=='SMOOTH':
            context.scene.free_ik.solver_mode=gv.smooth
        if self.mode=='ROPE':
            context.scene.free_ik.solver_mode=gv.rope

        if self.mode=='STRETCH_BOTH':
            context.scene.free_ik.solver_mode=gv.stretch
            context.scene.free_ik.stretch_mode=gv.stretch_both
        if self.mode=='STRETCH_HEAD':
            context.scene.free_ik.solver_mode=gv.stretch
            context.scene.free_ik.stretch_mode=gv.stretch_head
        if self.mode=='STRETCH_TAIL':
            context.scene.free_ik.solver_mode=gv.stretch
            context.scene.free_ik.stretch_mode=gv.stretch_tail


        return {'FINISHED'}

class SetLinkState(bpy.types.Operator):
    """Enable or disable selected links"""
    bl_idname="free_ik.set_link_state"
    bl_label="Set link state"
    bl_options={'REGISTER','UNDO'}

    link_state: bpy.props.BoolProperty(name="Enabled")

    @classmethod
    def poll(self,context):
        return True

    def check(self,context):
        return True

    def execute(self,context):
        pass  #print("EXECUTE")

        if context.mode=='POSE':
            work_objects=[]
            selected_pose_bones=set(context.selected_pose_bones)

            for link in gv.links:
                if link.node_a.source in selected_pose_bones and link.node_b.source in selected_pose_bones:
                    work_objects.append(link.source)

        elif context.mode=='OBJECT':
            work_objects=ontext.selected_objects

        for selected_object in work_objects:
            selected_object.free_ik.is_enabled=self.link_state
            selected_object.update_tag(refresh={'OBJECT'})
            pass  #print(selected_object.free_ik.is_enabled,self.link_state)

        # bpy.ops.free_ik.empty_operator()
        # gv.time_to_force_rebuild=True
        # validate_structure()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)
        # context.scene.update()

        return {'FINISHED'}


class SetPinState(bpy.types.Operator):
    """Pin or unpin selected"""
    bl_idname="free_ik.set_pin_state"
    bl_label="Set pin state"
    bl_options={'REGISTER','UNDO'}

    pin_state: bpy.props.BoolProperty(name="Pin state")

    @classmethod
    def poll(self,context):
        return True

    def execute(self,context):
        pass  #print("EXECUTE")

        if context.mode=='POSE':
            for selected_bone in context.selected_pose_bones:
                selected_bone.free_ik_is_pinned=self.pin_state
        if context.mode=='OBJECT':
            for selected_object in context.selected_objects:
                selected_object.free_ik_is_pinned=self.pin_state


        gv.time_to_force_rebuild=True
        validate_structure()
        for cluster in gv.clusters:
            cluster.update_state_scene()

        context.view_layer.update()
        update_colors()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)


        return {'FINISHED'}


class SetRigState(bpy.types.Operator):
    """Enable or disable rig"""
    bl_idname="free_ik.set_rig_state"
    bl_label="Set rig state"
    bl_options={'REGISTER','UNDO'}

    rig_state: bpy.props.BoolProperty(name="Rig state")

    @classmethod
    def poll(self,context):
        return True

    def execute(self,context):
        pass  #print("EXECUTE")

        work_items=[]

        if context.mode=='OBJECT':
            for selected_object in context.selected_objects:
                if type(selected_object.data)==bpy.types.Armature:
                    for pose_bone in selected_object.pose.bones:
                        if not pose_bone.bone.hide:
                            # if any([bl and al for bl,al in zip(pose_bone.bone.layers,selected_object.data.layers)]):
                            if len(pose_bone.bone.collections) == 0 or any(collection.is_visible for collection in pose_bone.bone.collections):
                                work_items.append(pose_bone)

                else:
                    if selected_object in gv.nodes_dictionary:
                        work_items.append(selected_object)

        if context.mode=='POSE':
            for pose_bone in context.selected_pose_bones:
                if pose_bone in gv.nodes_dictionary:
                    work_items.append(pose_bone)

        const_names=(gv.limit_location_name,gv.limit_rotation_name,gv.limit_scale_name)
        for item in work_items:

            item.id_data.update_tag(refresh={'OBJECT','DATA','TIME'})
            item.free_ik.is_rig_enabled=self.rig_state
            for const_name in const_names:
                if const_name in item.constraints:
                    item.constraints[const_name].mute=not self.rig_state



        context.view_layer.update()

        gv.time_to_force_rebuild=True
        validate_structure()

        for item in work_items:
            reset_color(item)

        update_colors()
        # bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)

        return {'FINISHED'}


class ClearParent(bpy.types.Operator):
    """Clear parent"""
    bl_idname="free_ik.clear_parent"
    bl_label="Clear parent"
    bl_options={'REGISTER','UNDO'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('POSE',"Pose parent","Clear pose parent",'NONE',0),
                                     ('FRAME',"Playback parent","Clear playback parent",'NONE',1),
                                 ]
                                 )

    @classmethod
    def poll(self,context):
        return True

    def execute(self,context):
        pass  #print("EXECUTE")

        active_item=None
        work_items=[]

        if context.mode=='POSE':
            active_item=context.active_pose_bone
            work_items.extend(context.selected_pose_bones)

        if context.mode=='OBJECT':
            active_item=context.object
            work_items.extend(context.selected_objects)

        if self.mode=='POSE': parent_name=gv.pose_parent_name
        if self.mode=='FRAME': parent_name=gv.frame_parent_name

        if active_item is not None:
            work_items.append(active_item)
        for item in work_items:
            if parent_name in item.constraints:
                pose_parent_holder=item.constraints[parent_name]
                pose_parent_holder.target=None
                pose_parent_holder.subtarget=""

        return {'FINISHED'}


class SetParent(bpy.types.Operator):
    """Set pose parent"""
    bl_idname="free_ik.set_parent"
    bl_label="Set parent"
    bl_options={'REGISTER','UNDO'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('POSE',"Pose parent","Set parent for posing",'NONE',0),
                                     ('FRAME',"Playback parent","Set parent for playback",'NONE',1),
                                 ]
                                 )

    direct: bpy.props.BoolProperty(name="Selected to active")

    def apply_parent(self,node):

        if self.mode=='POSE': parent_name=gv.pose_parent_name
        if self.mode=='FRAME': parent_name=gv.frame_parent_name

        if parent_name in node.source.constraints:
            parent_holder=node.source.constraints[parent_name]
        else:
            parent_holder=node.source.constraints.new('CHILD_OF')
            parent_holder.name=parent_name
            parent_holder.mute=True

        if node.pose_parent is None:
            parent_holder.target=None
            parent_holder.subtarget=""
        else:

            if type(node.pose_parent.source)==bpy.types.PoseBone:
                parent_holder.target=node.pose_parent.source.id_data
                parent_holder.subtarget=node.pose_parent.source.name
            else:
                parent_holder.target=node.pose_parent.source
                parent_holder.subtarget=""

        parent_holder.inverse_matrix=node.matrix

    @classmethod
    def poll(self,context):
        return True

    def execute(self,context):
        pass  #print("EXECUTE")

        active_object=None

        if context.mode=='POSE':
            active_object=context.active_pose_bone
            selected_objects=context.selected_pose_bones

        if context.mode=='OBJECT':
            active_object=context.object
            selected_objects=context.selected_objects

        pass  #print(active_object ,active_object in gv.nodes_dictionary)
        pass  #print(gv.nodes_dictionary.keys())

        if active_object in gv.nodes_dictionary:
            if gv.nodes_dictionary[active_object].cluster is not None:

                active_node=gv.nodes_dictionary[active_object]
                selected_nodes=set(gv.nodes_dictionary[selected_object] for selected_object in selected_objects if
                                   selected_object in gv.nodes_dictionary and gv.nodes_dictionary[
                                       selected_object].cluster is not None and selected_object!=active_object)

                if len(selected_nodes)!=0:

                    for node in gv.clustered_nodes:
                        node.is_selected=False

                    if active_node.pose_parent in selected_nodes:
                        active_node.pose_parent=None
                    for node in selected_nodes:
                        node.pose_parent=None

                    if self.direct:
                        for node in selected_nodes:
                            if active_node.cluster is node.cluster:
                                node.pose_parent=active_node
                    else:

                        last_nodes={active_node}  #type: List[Node]
                        while len(last_nodes)!=0:
                            next_nodes=set()
                            for last_node in last_nodes:
                                last_node.is_selected=True
                            for last_node in last_nodes:
                                for linked_node in last_node.linked_nodes:
                                    if not linked_node.is_selected and linked_node in selected_nodes:
                                        linked_node.pose_parent=last_node
                                        next_nodes.add(linked_node)
                            last_nodes=next_nodes

                self.apply_parent(active_node)
                for node in selected_nodes:
                    self.apply_parent(node)

                for node in selected_nodes:
                    pass  #print(node,'->',node.pose_parent)

        validate_structure()
        return {'FINISHED'}


# class CopyPoseReplacer(bpy.types.Operator):
#     bl_idname="free_ik.copy_pose_replacer"
#     bl_label="Copy Pose"
#     bl_options={'INTERNAL'}
#
#     def execute(self,context):
#         for node in gv.nodes:
#             node.copied_matrix[:]=node.get_matrix()
#         # print("POSE COPY")
#         bpy.ops.pose.copy()
#
#         return {'FINISHED'}


class CopyPoseReplacer(bpy.types.Operator):
    bl_idname="free_ik.copy_pose_replacer"
    bl_label="Copy Pose"
    bl_options={'INTERNAL'}

    def execute(self,context):

        # print("POSE COPY")
        bpy.ops.pose.copy()

        return {'FINISHED'}



class PastePoseReplacer(bpy.types.Operator):
    bl_idname="free_ik.paste_pose_replacer"
    bl_label="Paste Pose"
    bl_options={'INTERNAL','UNDO','REGISTER'}

    flipped: bpy.props.BoolProperty(name="Flipped on X-Axis",
                                    description="Paste the stored pose flipped on to current pose",default=False)
    selected_mask: bpy.props.BoolProperty(name="On Selected Only",
                                          description="Only paste the stored pose flipped on to selected bones in the current pose",
                                          default=False)

    def execute(self,context):
        pass  #print()
        pass  #print()
        pass  #print("PASTE BEGIN",random.randint(0,100))

        # validate_structure()
        gv.skip=True
        # context.scene.update()
        validate_structure()
        pass  #print(bpy.context.active_pose_bone.location)
        gv.is_pose_paste=True
        for node in gv.clustered_nodes:
            node.last.out_transform.from_node()
            node.rest_matrix[:]=node.get_matrix()

        before_transform_tuples=[get_transform_tuple(visible_pose_bone) for visible_pose_bone in
                                 context.visible_pose_bones]

        bpy.ops.pose.paste(flipped=self.flipped,selected_mask=False)

        pass  #print(bpy.context.active_pose_bone.location)

        for node in gv.clustered_nodes:
            node.copied_matrix[:]=node.get_matrix()
        if self.selected_mask:
            for visible_pose_bone,before_transform_tuple in zip(context.visible_pose_bones,before_transform_tuples):
                if not visible_pose_bone.bone.select:
                    # pass#print(visible_pose_bone.name)
                    apply_transform_tuple(visible_pose_bone,before_transform_tuple)
            context.view_layer.update()
        gv.skip=False
        # gv.time_to_force_solve=True
        pass  #print("FINAL UPDATE")
        bpy.ops.pose.paste(flipped=self.flipped,selected_mask=self.selected_mask)
        # context.scene.update()
        gv.is_pose_paste=False
        # gv.time_to_force_solve=False

        # print("PASTE END")

        return {'FINISHED'}


class TransformReplacer(bpy.types.Operator):
    bl_idname="free_ik.transform_replacer"
    bl_label="Transform replacer"
    bl_options={'INTERNAL'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('TRANSLATE',"Translate","Translate",'NONE',0),
                                     ('ROTATE',"Rotate","Rotate",'NONE',1),
                                     ('RESIZE',"Resize","Resize",'NONE',2),
                                     ('MIRROR',"Mirror","Mirror",'NONE',3),
                                     ('BREAKDOWN',"","",'NONE',4),
                                     ('GIZMO',"","",'NONE',5),
                                 ]
                                 )

    def execute(self,context):
        # print("TRANSFORM START")

        for node in gv.clustered_nodes:
            # node.modal_start_transform.from_node()
            node.modal_start_transform.from_other(node.last.out_transform)


        for node in gv.clustered_nodes:
            matrix=node.get_matrix()
            node.rest_matrix[:]=matrix
            node.smooth_rest_matrix[:]=matrix
            node.modal_start_matrix[:]=matrix
            node.shift_matrix[:]=mathutils.Matrix.Identity(4)

            # node.last.in_transform.from_node()

        gv.is_modal_transform=True


        gv.modal_start_operator=bpy.context.active_operator
        bpy.ops.blendamin.transform_end('INVOKE_DEFAULT')

        try:
            if self.mode == 'TRANSLATE':
                bpy.ops.transform.translate('INVOKE_DEFAULT')
            if self.mode == 'ROTATE':
                bpy.ops.transform.rotate('INVOKE_DEFAULT')
            if self.mode == 'RESIZE':
                bpy.ops.transform.resize('INVOKE_DEFAULT')
            if self.mode == 'MIRROR':
                bpy.ops.transform.mirror('INVOKE_DEFAULT')

            if self.mode == 'GIZMO':
                bpy.ops.gizmogroup.gizmo_tweak('INVOKE_DEFAULT')

        except:
            pass

        if self.mode == 'BREAKDOWN':
            try:
                bpy.ops.pose.breakdown('INVOKE_DEFAULT')
            except RuntimeError as error:
                self.report({'ERROR'}, str(error).split(':')[1][1:-1])

        pass  #print("TRANSFORM START")
        return {'FINISHED'}


class TransformEnd(bpy.types.Operator):
    bl_idname='blendamin.transform_end'
    bl_label='Transform end'
    bl_options={'INTERNAL'}

    def execute(self,context):
        return {'FINISHED'}

    def modal(self,context,event):
        # print("----",event.type, event.value)


        gv.is_modal_transform=True

        if event.type not in ('TIMER','TIMER0'):
            if gv.modal_start_operator==context.active_operator:
                # print("TRANSFORM CANCEL")
                for node in gv.clustered_nodes:
                    node.modal_start_transform.apply_to_limit()
                    node.modal_start_transform.apply_to_base()
                    node.last.out_transform.from_other(node.modal_start_transform)
                    node.last.in_transform.from_other(node.modal_start_transform)
                    node.default_transform.from_other(node.modal_start_transform)
                    gv.last_operator=None
                    matrix=node.get_matrix()
                    node.last.out_matrix[:]=matrix
                    node.rest_matrix[:]=matrix


            else:
                pass  #print("TRANSFORM CONFIRM")

            for node in gv.clustered_nodes:
                matrix=node.get_matrix()
                node.rest_matrix[:]=matrix

                node.last.in_transform.from_other(node.last.out_transform)
                node.default_transform.from_other(node.last.out_transform)






            gv.is_modal_transform=False

            # print("TRANSFORM FINISHED")
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self,context,event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class GraphTransformReplacer(bpy.types.Operator):
    bl_idname="free_ik.graph_transform_replacer"
    bl_label="Transform replacer"
    bl_options={'INTERNAL'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('TRANSLATE',"Translate","Translate",'NONE',0),
                                     ('ROTATE',"Rotate","Rotate",'NONE',1),
                                     ('RESIZE',"Resize","Resize",'NONE',2),
                                 ]
                                 )

    def execute(self,context):

        # print("GRAPH TRANSFORM START")
        gv.modal_start_operator=bpy.context.active_operator
        bpy.ops.blendamin.graph_transform_end('INVOKE_DEFAULT')

        if self.mode=='TRANSLATE':
            bpy.ops.transform.translate('INVOKE_DEFAULT')
        if self.mode=='ROTATE':
            bpy.ops.transform.rotate('INVOKE_DEFAULT')
        if self.mode=='RESIZE':
            bpy.ops.transform.resize('INVOKE_DEFAULT')

        pass  #print("TRANSFORM START")
        return {'FINISHED'}


class GraphTransformEnd(bpy.types.Operator):
    bl_idname='blendamin.graph_transform_end'
    bl_label='Transform end'
    bl_options={'INTERNAL'}

    def execute(self,context):
        return {'FINISHED'}

    def modal(self,context,event):
        pass  #print("----",event.type, event.value)

        if event.type!='TIMER':

            if gv.modal_start_operator==context.active_operator:
                pass
                # print("GRAPH TRANSFORM CANCEL")

            else:
                pass
                # print("GRAPH TRANSFORM CONFIRM")

            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self,context,event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class DopeSheetTransformReplacer(bpy.types.Operator):
    bl_idname="free_ik.dope_sheet_transform_replacer"
    bl_label="Transform replacer"
    bl_options={'INTERNAL'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('TRANSLATE',"Translate","Translate",'NONE',0),
                                     ('EXTEND',"Extend","Extend",'NONE',1),
                                     ('SCALE',"Scale","Scale",'NONE',2),
                                     ('SLIDE',"Slide","Slide",'NONE',3),
                                 ]
                                 )

    def execute(self,context):

        # print("DOPE SHEET REPLACER")
        gv.is_curve_change=True
        gv.modal_start_operator=context.active_operator
        bpy.ops.blendamin.dope_sheet_transform_end('INVOKE_DEFAULT')

        if self.mode=='TRANSLATE':
            bpy.ops.transform.transform('INVOKE_DEFAULT',mode='TIME_TRANSLATE')
        if self.mode=='EXTEND':
            bpy.ops.transform.transform('INVOKE_DEFAULT',mode='TIME_EXTEND')
        if self.mode=='SCALE':
            bpy.ops.transform.transform('INVOKE_DEFAULT',mode='TIME_SCALE')
        if self.mode=='SLIDE':
            bpy.ops.transform.transform('INVOKE_DEFAULT',mode='TIME_SLIDE')

        return {'FINISHED'}


class DopeSheetTransformEnd(bpy.types.Operator):
    bl_idname='blendamin.dope_sheet_transform_end'
    bl_label='Transform end'
    bl_options={'INTERNAL'}

    def execute(self,context):
        return {'FINISHED'}

    def modal(self,context,event):
        pass  #print("----",event.type, event.value)

        if event.type!='TIMER':
            if gv.modal_start_operator==context.active_operator:
                pass
                # print("DOPE SHEET REPLACER CANCEL")


            else:
                pass
                # print("DOPE SHEET REPLACER CONFIRM")

            gv.is_curve_change=False
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self,context,event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}










class NLATransformReplacer(bpy.types.Operator):
    bl_idname="free_ik.nla_transform_replacer"
    bl_label="Transform replacer"
    bl_options={'INTERNAL'}

    mode: bpy.props.EnumProperty(name="Mode",
                                 items=[
                                     ('TRANSLATE',"Translate","Translate",'NONE',0),
                                     ('EXTEND',"Extend","Extend",'NONE',1),
                                     ('SCALE',"Scale","Scale",'NONE',2),
                                     ('SLIDE',"Slide","Slide",'NONE',3),
                                 ]
                                 )

    def execute(self,context):

        # print("NLA REPLACER")
        gv.is_nla_modal=True

        gv.modal_start_operator=context.active_operator

        bpy.ops.blendamin.nla_transform_end('INVOKE_DEFAULT')

        if self.mode=='TRANSLATE':
            bpy.ops.transform.transform('INVOKE_DEFAULT',mode='TRANSLATION')
        if self.mode=='EXTEND':
            bpy.ops.transform.transform('INVOKE_DEFAULT',mode='TIME_EXTEND')
        if self.mode=='SCALE':
            bpy.ops.transform.transform('INVOKE_DEFAULT',mode='TIME_SCALE')


        return {'FINISHED'}


class NLATransformEnd(bpy.types.Operator):
    bl_idname='blendamin.nla_transform_end'
    bl_label='Transform end'
    bl_options={'INTERNAL'}

    def execute(self,context):
        return {'FINISHED'}

    def modal(self,context,event):
        pass  #print("----",event.type, event.value)

        if event.type!='TIMER':
            if gv.modal_start_operator==context.active_operator:
                pass
                # print("NLA REPLACER CANCEL")


            else:
                pass
                # print("NLA REPLACER CONFIRM")

            gv.is_nla_modal=False
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self,context,event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}








def getattr_nested(source,path):
    splitted=path.split(".")

    out_source=source
    for name in splitted[:-1]:
        if hasattr(out_source,name):
            out_source=getattr(out_source,name)
        else:
            return None
    if hasattr(out_source,splitted[-1]):
        return getattr(out_source,splitted[-1])


def setattr_nested(source,path,value):
    splitted=path.split(".")

    out_source=source
    for name in splitted[:-1]:
        if hasattr(out_source,name):
            out_source=getattr(out_source,name)
        else:
            return None
    if hasattr(out_source,splitted[-1]):
        setattr(out_source,splitted[-1],value)


def make_keys():
    # print("MAKE KEYS")

    gv.keymaps={
        '3D View':(
            ({"idname":"transform.translate","properties.texture_space":False,"properties.gpencil_strokes":False},
             {"idname":TransformReplacer.bl_idname,"properties.mode":'TRANSLATE'}),
            ({"idname":"transform.rotate","properties.gpencil_strokes":False},
             {"idname":TransformReplacer.bl_idname,"properties.mode":'ROTATE'}),
            ({"idname":"transform.resize","properties.texture_space":False,"properties.gpencil_strokes":False},
             {"idname":TransformReplacer.bl_idname,"properties.mode":'RESIZE'}),
            ({"idname":"transform.mirror","properties.gpencil_strokes":False},
             {"idname":TransformReplacer.bl_idname,"properties.mode":'MIRROR'}),

        ),

        'Object Mode': (
            ({"idname": "transform.translate", "properties.texture_space": False, "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'TRANSLATE'}),
            ({"idname": "transform.rotate", "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'ROTATE'}),
            ({"idname": "transform.resize", "properties.texture_space": False, "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'RESIZE'}),
            ({"idname": "transform.mirror", "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'MIRROR'}),

        ),

        'Pose':(
            # ({"idname":"pose.paste"},{"idname":PastePoseReplacer.bl_idname}),
            # ({"idname":"pose.copy"},{"idname":CopyPoseReplacer.bl_idname}),

            ({"idname":"pose.paste","properties.flipped":False},{"idname":PastePoseReplacer.bl_idname,"properties.flipped":False}),
            ({"idname":"pose.paste","properties.flipped":True},{"idname":PastePoseReplacer.bl_idname,"properties.flipped":True}),

            ({"idname": "transform.translate", "properties.texture_space": False, "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'TRANSLATE'}),
            ({"idname": "transform.rotate", "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'ROTATE'}),
            ({"idname": "transform.resize", "properties.texture_space": False, "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'RESIZE'}),
            ({"idname": "transform.mirror", "properties.gpencil_strokes": False},
             {"idname": TransformReplacer.bl_idname, "properties.mode": 'MIRROR'}),


        ),

        'Generic Gizmo Maybe Drag':(

            (
                {"idname":"gizmogroup.gizmo_tweak"},
                {"idname":TransformReplacer.bl_idname,"properties.mode":'GIZMO'}),

        ),



    }

    if bpy.context.window_manager.keyconfigs.active is not None:
        gv.keyconfig=bpy.context.window_manager.keyconfigs.active

    else:
        gv.keyconfig=bpy.context.window_manager.keyconfigs.default
        # print("AAA")



    to_create=[]
    for keymap in gv.keymaps:
        if keymap not in gv.keyconfig.keymaps:keymap_items=gv.keyconfig.keymaps.new(keymap).keymap_items
        else:keymap_items=gv.keyconfig.keymaps[keymap].keymap_items


        for keymap_item in keymap_items:
            for to_replace_settings,replacer_settings in gv.keymaps[keymap]:
                match=True
                for key,value in to_replace_settings.items():
                    if getattr_nested(keymap_item,key)!=value:
                        match=False
                        break
                if match:
                    to_create.append((keymap_items,keymap_item,replacer_settings))




    for keymap_items,keymap_item,replacer_settings in to_create:
        # print(keymap_items,keymap_item,replacer_settings)
        item=keymap_items.new_from_item(keymap_item,head=True)

        for key,value in replacer_settings.items():
            setattr_nested(item,key,value)

    gv.time_to_make_keys=False


def clear_keys():
    # print("CLEAR KEYS")

    to_delete=[]
    if gv.keymaps is not None:
        for keymap in gv.keymaps:
            keymap_items=gv.keyconfig.keymaps[keymap].keymap_items
            for keymap_item in keymap_items:
                for to_replace_settings,replacer_settings in gv.keymaps[keymap]:
                    match=True
                    for key,value in replacer_settings.items():
                        if getattr_nested(keymap_item,key)!=value:
                            match=False
                            break
                    if match:
                        to_delete.append((keymap_items,keymap_item))

        for keymap_items,keymap_item in to_delete:
            keymap_items.remove(keymap_item)


@persistent
def render_before_handler(scene):
    # print("RENDER BEFORE")
    gv.is_rendering=True
    # set_limits_state(False)
    # reset_structure()
    # gv.time_to_force_rebuild=True
    # validate_structure()
    # validate_frame()


@persistent
def render_after_handler(scene):
    # print("RENDER AFTER")
    gv.is_rendering=False
    # set_limits_state(True)

@persistent
def render_pre_handler(scene):
    pass
    # print("RENDER PRE")

    # bpy.context.scene.update_tag(refresh={'TIME'})
    # for node in gv.clustered_nodes:
    #     node.default_transform.apply_to_base()
        # node.source.id_data.update_tag(refresh={'TIME'})



def make_render_handlers():
    pass  #print("REGISTER RENDER HANDLERS")
    bpy.app.handlers.render_init.append(render_before_handler)
    bpy.app.handlers.render_pre.append(render_before_handler)

    bpy.app.handlers.render_post.append(render_after_handler)
    bpy.app.handlers.render_cancel.append(render_after_handler)
    bpy.app.handlers.render_complete.append(render_after_handler)
    bpy.app.handlers.render_write.append(render_after_handler)


def make_handlers():
    bpy.app.handlers.depsgraph_update_pre.append(scene_before_handler)
    bpy.app.handlers.depsgraph_update_post.append(scene_after_handler)
    #
    bpy.app.handlers.frame_change_pre.append(frame_change_before_handler)
    bpy.app.handlers.frame_change_post.append(frame_change_after_handler)

    # bpy.app.handlers.load_pre.append(load_before_handler)
    bpy.app.handlers.load_post.append(validation_handler)

    # bpy.app.handlers.load_factory_startup_post.append(load_after_handler)
    bpy.app.handlers.redo_post.append(validation_handler)
    bpy.app.handlers.undo_post.append(validation_handler)

    bpy.app.handlers.render_init.append(render_before_handler)

    bpy.app.handlers.render_pre.append(render_pre_handler)
    # bpy.app.handlers.render_pre.append(frame_change_after_handler)

    # bpy.app.handlers.render_post.append(render_after_handler)
    bpy.app.handlers.render_cancel.append(render_after_handler)
    bpy.app.handlers.render_complete.append(render_after_handler)
    # bpy.app.handlers.render_write.append(render_after_handler)


def clear_handlers():
    bpy.app.handlers.depsgraph_update_pre.remove(scene_before_handler)
    bpy.app.handlers.depsgraph_update_post.remove(scene_after_handler)
    #
    bpy.app.handlers.frame_change_pre.remove(frame_change_before_handler)
    bpy.app.handlers.frame_change_post.remove(frame_change_after_handler)

    # bpy.app.handlers.load_pre.append(load_before_handler)
    bpy.app.handlers.load_post.remove(validation_handler)
    # bpy.app.handlers.load_factory_startup_post.append(load_after_handler)
    bpy.app.handlers.redo_post.remove(validation_handler)
    bpy.app.handlers.undo_post.remove(validation_handler)

    bpy.app.handlers.render_init.remove(render_before_handler)

    bpy.app.handlers.render_pre.remove(render_pre_handler)
    # bpy.app.handlers.render_pre.remove(frame_change_after_handler)

    # bpy.app.handlers.render_post.remove(render_after_handler)
    bpy.app.handlers.render_cancel.remove(render_after_handler)
    bpy.app.handlers.render_complete.remove(render_after_handler)
    # bpy.app.handlers.render_write.remove(render_after_handler)


def show_overlays_draw(self,context):
    self.layout.prop(context.scene.free_ik,"show_overlays")


def transform_extender(self,context,item):
    if item in gv.nodes_dictionary:
        if gv.nodes_dictionary[item].frame_parent is not None:
            if item.rotation_mode=='QUATERNION':
                self.layout.prop(item,"free_ik_local_quaternion")
            elif item.rotation_mode=='AXIS_ANGLE':
                self.layout.prop(item,"free_ik_local_axis_angle")
            else:
                self.layout.prop(item,"free_ik_local_euler")


def bone_transform_extender(self,context):
    transform_extender(self,context,context.active_pose_bone)


def object_transform_extender(self,context):
    transform_extender(self,context,context.object)


class VIEW3D_PT_free_ik_overlay(bpy.types.Panel):
    bl_space_type='VIEW_3D'
    bl_region_type='HEADER'
    bl_parent_id='VIEW3D_PT_overlay'
    # bl_parent_id='FreeIKParentingMenu'
    bl_label=""

    def draw_header(self,context):
        pass
        self.layout.label(text="FreeIK")
        # self.layout.prop(context.scene.free_ik,"show_overlays")

    def draw(self,context):
        pass
        row=self.layout.row()
        row.prop(context.scene.free_ik,"show_generic")
        row.prop(context.scene.free_ik,"show_pinned")
        # self.layout.prop(context.scene.free_ik,"show_overlays")


paint_holder=set()


def paint_lines():
    # pass#print(bpy.context.space_data.overlay.show_overlays)
    if bpy.context.mode in ('OBJECT','POSE') and bpy.context.space_data.overlay.show_overlays and (
            bpy.context.scene.free_ik.show_generic or bpy.context.scene.free_ik.show_pinned):

        points=[]
        colors=[]
        indices=[]
        points_count=0

        nodes=[]
        pinned_nodes=[]
        for node in gv.clustered_nodes:
            if (node.is_bone and bpy.context.space_data.show_object_viewport_armature) or (
                    not node.is_bone and bpy.context.space_data.show_object_viewport_mesh):
                if node.is_visible:
                    if node.is_pinned and bpy.context.scene.free_ik.show_pinned:
                        pinned_nodes.append(node)
                    elif not node.is_pinned and bpy.context.scene.free_ik.show_generic:
                        nodes.append(node)
        nodes=nodes+pinned_nodes

        for node in nodes:
            matrix=node.source.matrix_world

            if node.is_pinned:
                color=(1,0,0,1)
            else:
                color=(0,0,0,0.4)

            if len(node.points)==1:
                node_points=node.points+list(node.fallback_points)
            else:
                node_points=node.points

            for x in range(len(node_points)):
                points.append(tuple(matrix@node_points[x]))
                colors.append(color)
                for y in range(len(node_points)):
                    indices.append((points_count+x,points_count+y))

            points_count+=len(node_points)

        # bgl.glEnable(bgl.GL_BLEND)
        gpu.state.blend_set('ALPHA')

        # bgl.glDisable(bgl.GL_DEPTH_TEST)
        gpu.state.depth_mask_set(False)


        width=2

        # bgl.glLineWidth(width)
        gpu.state.line_width_set(width)

        # bgl.glPointSize(width*2)
        gpu.state.point_size_set(width*2)

        shader=gpu.shader.from_builtin('FLAT_COLOR')
        shader.bind()

        lines_batch=batch_for_shader(gv.shader,'LINES',{"pos":points,"color":colors},indices=indices)
        lines_batch.draw(gv.shader)
        points_batch=batch_for_shader(gv.shader,'POINTS',{"pos":points,"color":colors})
        points_batch.draw(gv.shader)


register_classes=[FreeIKNodeSettings,FreeIKConstraintPanel,FreeIKSceneSettings,FreeIKScenePanel,MakeLinks,ClearLinks,FreeIKObjectPanel,FreeIKBonePanel]
register_classes.extend([TransformReplacer,TransformEnd])
register_classes.extend([CopyPoseReplacer,PastePoseReplacer])
register_classes.extend([Bake,Keyframer])
register_classes.extend([FREEIK_MT_FreeIKPieMenu,FreeIKPieMenuStarter,FREEIK_PT_FreeIKParentingMenu,FREEIK_MT_ChangeMode,FreeIKChangeModeStarter])
register_classes.extend([SetParent,ClearParent])
register_classes.extend([SetPinState,SetLinkState,SetRigState,SetSolverMode])
register_classes.extend([VIEW3D_PT_free_ik_overlay])
register_classes.extend([KeyMapOperator,Preferences])
register_classes.extend([DopeSheetTransformReplacer,DopeSheetTransformEnd])
register_classes.extend([GraphTransformReplacer,GraphTransformEnd])
register_classes.extend([NLATransformReplacer,NLATransformEnd])

def register():
    # os.system('cls')
    # print("I AM REGISTER")

    make_handlers()

    for register_class in register_classes:
        bpy.utils.register_class(register_class)

    register_extensions()
    gv.time_to_force_rebuild=True
    gv.time_to_update_drivers=True
    gv.time_to_make_keys=True


    paint_holder.add(bpy.types.SpaceView3D.draw_handler_add(paint_lines,(),'WINDOW','POST_VIEW'))

    # bpy.app.timers.register(modal_timer)

    pass  #print("REGISTER FINISHED")


def unregister():
    pass  #print("I AM UNREGISTER")

    validate_structure()
    pass  #print("AAA",len(gv.nodes))
    # set_limits_state(False)
    gv.time_to_update_drivers=False
    bpy.context.view_layer.update()

    for item in paint_holder:
        bpy.types.SpaceView3D.draw_handler_remove(item,'WINDOW')
    unregister_extensions()

    paint_holder.clear()
    clear_keys()

    for register_class in reversed(register_classes):
        bpy.utils.unregister_class(register_class)

    clear_handlers()

    # bpy.app.timers.unregister(modal_timer)

    pass  #print("UNREGISTER FINISHED")


