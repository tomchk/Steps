bl_info = {
    "name": "Steps Tracker",
    "blender": (4, 0, 0),
    "category": "Object",
    "author": "Tracy Wankio",
    "version": (1, 0),
}


import bpy
import copy
import math
from itertools import zip_longest



previous_mesh_info = {}
previous_location = None
starting_location = None
starting_rotation= None
previous_rotation= None
starting_scale=None
previous_scale= None
steps = []
logged_op = None
translation= False
initial_mat= None
mat_change=False
slot_ids={}
initial_mods={}
recording= False
steps_recorded=False

def get_starting_loc():
    global starting_location
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':       
        starting_location = ( copy.deepcopy(obj.location), True) 
       
        

def get_pos_transform (start, end):
    
    global steps
    
    
    
    translation = tuple(e - s for e, s in zip(end, start))

    
    command = (
        f"bpy.ops.transform.translate("
        f"value=({translation[0]}, {translation[1]}, {translation[2]}), "
        f"orient_type='GLOBAL', "
        f"orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), "
        f"orient_matrix_type='GLOBAL', "
        f"mirror=False, "
        f"use_proportional_edit=False, "
        f"proportional_edit_falloff='SMOOTH', "
        f"proportional_size=1, "
        f"use_proportional_connected=False, "
        f"use_proportional_projected=False, "
        f"snap=False, "
        f"snap_elements={{'INCREMENT'}}, "
        f"use_snap_project=False, "
        f"snap_target='CLOSEST', "
        f"use_snap_self=True, "
        f"use_snap_edit=True, "
        f"use_snap_nonedit=True, "
        f"use_snap_selectable=False, "
        f"alt_navigation=True)"
    )

    steps.append(command)
    return command


def get_starting_rotation():
    global starting_rotation
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':  
        
        rot = obj.rotation_euler
        
        # Extract rotations around X, Y, and Z axes (in radians)
        rotation_x = rot.x
        rotation_y = rot.y
        rotation_z = rot.z
        
        rotation= (rotation_x , rotation_y , rotation_z )     
        
        starting_rotation = copy.deepcopy(rotation)
    
        

def rotation_command (start, end):
    
    global steps
    global starting_rotation
 
    
    if end is not None and start is not None and len(end) == len(start):
        rotation = tuple(e - s for e, s in zip(end, start))
    
    else:


        rotation = None  
 
    
 
    if rotation[0] != 0:  # X-axis rotation
        command_x = (
            f"bpy.ops.transform.rotate(value={-(rotation[0])}, "
            f"orient_axis='X')"
        )
        steps.append(command_x)

    if rotation[1] != 0:  # Y-axis rotation
        command_y = (
            f"bpy.ops.transform.rotate(value={-(rotation[1])}, "
            f"orient_axis='Y')"
        )
        steps.append(command_y)

    if rotation[2] != 0:  # Z-axis rotation
        command_z = (
            f"bpy.ops.transform.rotate(value={-(rotation[2])}, "
            f"orient_axis='Z')"
        )
        steps.append(command_z)
        
        

def get_starting_scale():
    global starting_scale
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':       
        starting_scale = copy.deepcopy(obj.scale)
  
        

def get_scale_factor(start, end):
    
    global steps

    factor = tuple(e / s for e, s in zip(end, start))

    
    command = (
    f"bpy.ops.transform.resize("
    f"value=({factor[0]}, {factor[1]}, {factor[2]}), "
    f"orient_type='GLOBAL')"
)


    steps.append(command)
    return command
    


    

def log_mesh_changes(dummy):
    
    obj = bpy.context.active_object
    
    
    global logged_op
    global translation
    global previous_mesh_info
    global previous_location
    global starting_location
    global starting_scale
    global previous_rotation
    global previous_scale
    
    
    
    if obj and obj.type == 'MESH':
        
       
        last_operator = bpy.context.window_manager.operators[-1].bl_idname
        
       
        if last_operator != logged_op:
         
            
            logged_op=last_operator
            
            #check if operator was a translation one
            if last_operator == 'TRANSFORM_OT_translate':
                translation = True
            
        # Track mesh modifications (vertices, edges, faces)
        mesh_data = obj.data
        vertices_count = len(mesh_data.vertices)
        edges_count = len(mesh_data.edges)
        faces_count = len(mesh_data.polygons)
        
        mesh_changes = {
            'vertices': vertices_count,
            'edges': edges_count,
            'faces': faces_count
        }
        
        if previous_mesh_info:
            # Compare previous state with current state
            for key, value in mesh_changes.items():
                if previous_mesh_info.get(key) != value:
                    print(f' Debug  key: {previous_mesh_info.get(key)} value: {value}')
                    print(f"Mesh {key} count changed: {value}")
                    
             
        
        previous_mesh_info.update(mesh_changes)
        
      
        current_location = obj.location
        if current_location != previous_location:
            previous_location = copy.copy(current_location)
            locationchange= (True , {last_operator}) 
        
        
        current_rotation = obj.rotation_euler
        
        rotation_x = current_rotation.x
        rotation_y = current_rotation.y
        rotation_z = current_rotation.z
        
        current_rotation= (rotation_x , rotation_y , rotation_z )
        if current_rotation != previous_rotation:    
            
            previous_rotation = copy.copy(current_rotation)
            rotationchange= (True , {last_operator}) 
            
        #Scale   
        current_scale = obj.scale
        if current_scale != previous_scale:        
            previous_scale = copy.copy(current_scale)
            
    
            
def get_mat_command(current_mat, initial_mat):
    obj = bpy.context.active_object 
  
    
  
    
   
    #get the loop count to avoid checking past the material slots
    #this code will have to be done when applying
    min_length = min(len(current_mat), len(initial_mat))
   
    
    zipped_lists = zip_longest(current_mat, initial_mat, fillvalue=None)

    
    #get the material slot that changed
    global slot_ids
    slot_ids = {}
    for i, (current_val, initial_val) in enumerate(zipped_lists):
        if current_val != initial_val:
            slot_ids[i] = (current_val, initial_val)
            global mat_change
            mat_change= True
  
def apply_mat_command(slot_ids):
    global mat_change
    if mat_change:
        command = ""
        for slot_id, (current_material, initial_material) in slot_ids.items():
            if current_material == None:
                command+=(
                f"bpy.context.object.active_material_index={slot_id}\n"
                f"bpy.ops.object.material_slot_remove()")
                
            else:
                if slot_id < len(bpy.context.object.material_slots):
                    command += (
                        f"bpy.context.object.material_slots[{slot_id}].material = bpy.data.materials['{current_material.name}']\n"
                    )
                else:
                    command += (
                        f"bpy.ops.object.material_slot_add()\n"
                        f"bpy.context.object.material_slots[-1].material = bpy.data.materials['{current_material.name}']\n"
                    )
            
       
        
        global steps
        steps.append(command)
        
def get_mod_props():
    mod_props = {}  # Assuming mod_props is a dictionary declared somewhere

    obj = bpy.context.active_object

    for modifier in bpy.context.object.modifiers:
        allprops = dir(bpy.context.object.modifiers[modifier.name])
        moddict = {}

        for prop in allprops:
            value = getattr(obj.modifiers[modifier.name], prop, None)
            moddict[prop] = value
        mod_props[modifier.name] = moddict
    return mod_props



def compare_dicts(a, b):
    
    global steps

    for key in b.keys():
      if key not in a :
        mod=bpy.context.object.modifiers[key].type
        command=(f"bpy.ops.object.modifier_add(type='{mod}')")
        steps.append(command)
        for prop in (b[key]).keys():
            if prop not in ["__doc__","name","custom_profile", "rna_type","type", "is_override_data", "__module__", "__slots__", "bl_rna", "damping_time", "execution_time"]:
                value_str = f"'{b[key][prop]}'" if isinstance(b[key][prop], str) else b[key][prop]
                command = f"bpy.context.object.modifiers['{key}'].{prop} = {value_str}"
                steps.append(command)

        if key in a:
          print (b[key])
          
          for prop in (b[key]).keys():
            
            if b[key][prop] != a[key][prop]:
              print(f"Modifier {key} value {prop} changed from {a[key][prop]} to {b[key][prop]}")

        #check if a modifier has been removed
    for key in a .keys():  
        if key not in b:
            print(f"Modifier {key} has been removed")
    
            command = f"bpy.ops.object.modifier_remove(modifier='{key}')"
            steps.append(command)

class StartOperator(bpy.types.Operator):
    bl_idname = "myaddon.start"
    bl_label = "Track"

    
    def invoke(self, context, event):
            wm = context.window_manager
            return wm.invoke_popup(self, width=240)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Click on a mesh object to start recording")
    

    
    def execute(self, context):
       
        global steps
        
        # Clear the steps list before starting a new recording
        steps.clear()
        
        global starting_location
        get_starting_loc()
        get_starting_rotation()
        get_starting_scale()
        
        
        # Register the handler to monitor changes
        bpy.app.handlers.depsgraph_update_post.append(log_mesh_changes)
        
        # Register the material changes
        global initial_mat
        obj = bpy.context.active_object
    
        if obj and obj.type == 'MESH':
            initial_mat=obj.data.materials[:]
            global initial_mods
            initial_mods=get_mod_props()
            
        #set recording state to True
        global recording
        global steps_recorded
        recording= True
        steps_recorded=False
        return {'FINISHED'}
    
class StopOperator(bpy.types.Operator):
    bl_idname = "myaddon.stop"
    bl_label = "Stop"
    
    
    
    def execute(self, context):
        
        
        
        global translation
        global steps
        global starting_rotation
        global starting_scale
        
        obj = bpy.context.active_object
    
        if obj and obj.type == 'MESH':
            global starting_location
           
        
            if translation:
                get_pos_transform (starting_location[0], obj.location)
                
        #update rotation steps
        
            current_rotation = obj.rotation_euler
        
            # Extract rotations around X, Y, and Z axes (in radians)
            rotation_x = current_rotation.x
            rotation_y = current_rotation.y
            rotation_z = current_rotation.z
            
            current_rotation =(rotation_x , rotation_y , rotation_z)
        
            if current_rotation != starting_rotation:
                rotation_command (starting_rotation, current_rotation)
                
            #scale
            current_scale=obj.scale
            if current_scale != starting_scale:
                get_scale_factor (starting_scale, current_scale)
                
                
                
                
            #check if material changed
            current_mat=obj.data.materials[:]
            if current_mat != initial_mat:
                get_mat_command(current_mat, initial_mat)
                
                
            #check if modifiers have changed
            global initial_mods
            current_mods=get_mod_props()
            if current_mods == initial_mods:
                print (f"MODS STAYED THE SAME")
            else:
                compare_dicts(initial_mods, current_mods)
                
        
        
        
                
        for step in steps:        
            print(f" STEPS {step} \n")
        
        global recording
        global steps_recorded
        steps_recorded=True
        recording = False
        print('Steps recorded: True')
            
        return {'FINISHED'}
    
class ApplyOperator(bpy.types.Operator):
    bl_idname = "myaddon.apply"
    bl_label = "Apply"
    
    def execute(self, context):
       
        global steps
        
        apply_mat_command(slot_ids)
        
        for command in steps:
            exec(command)
            
       
        
        return {'FINISHED'}
    
class ExportOperator(bpy.types.Operator):
    bl_idname = "myaddon.export"
    bl_label = "Export"
    
    def execute(self, context):
        global steps
       
        filepath = "saved_steps.py" 
        
        # Open the file in write mode
        with open(filepath, "w") as file:
            # Write each step from the 'steps' variable to the file
            for step in steps:
                file.write(step + "\n")  # Write each step followed by a newline
        return {'FINISHED'}

class StepsTracker(bpy.types.Panel):
    """Creates a Panel in the scene context of the View3d editor"""
    bl_label = "Steps Tracker"
    bl_idname = "STEP5_PT_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Steps Tracker"
    
    

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text=" Hit Track to Start tracking your steps")


        # Big render buttonn
        global recording
        global steps_recorded
       
        row = layout.row()
        row.scale_y = 1.5
        if not recording:
            row.operator("myaddon.start")
            row.enabled=True
        else:
            row.operator("myaddon.start", text="Recording...")
            row.enabled = False


        # Different sizes in a row
        layout.label(text="Next")
        row = layout.row(align=True)
        sub3=row.row()
        if recording:
            sub3.operator("myaddon.stop")
            sub3.enabled = True
        else:
            sub3.operator("myaddon.stop")
            sub3.enabled=False


        sub = row.row()
        sub.scale_x = 2.0
        sub.operator("myaddon.apply")
        sub2 = row.row()
        sub2.operator("myaddon.export")
        if steps_recorded:
            sub2.enabled=True
            sub.enabled=True
        else:
            sub2.enabled=False
            sub.enabled=False


def register():
    bpy.utils.register_class(StartOperator) 
    bpy.utils.register_class(StopOperator)
    bpy.utils.register_class(ApplyOperator)
    bpy.utils.register_class(ExportOperator)
    bpy.utils.register_class(StepsTracker)


def unregister():
    bpy.utils.unregister_class(StartOperator)
    bpy.utils.unregister_class(StopOperator)
    bpy.utils.unregister_class(ApplyOperator)
    bpy.utils.unregister_class(ExportOperator)
    bpy.utils.unregister_class(StepsTracker)


if __name__ == "__main__":
   
    register()
