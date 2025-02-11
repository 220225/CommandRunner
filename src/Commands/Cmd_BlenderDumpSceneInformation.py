import json
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import suppress

with suppress(ModuleNotFoundError):
    import bpy

import Core

logger = Core.get_logger()

from CommandBase import CommandBase

def get_object_info(obj):
    info = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "visible": obj.visible_get()
    }
    info["custom_properties"] = {k: str(v) for k, v in obj.items()}
    return info

def get_material_info(mat):
    return {
        "name": mat.name,
        "use_nodes": mat.use_nodes,
        "blend_method": mat.blend_method
    }

def get_scene_info():
    scene_info = {}
    
    scene_info["objects"] = [get_object_info(obj) for obj in bpy.data.objects]
        
    scene_info["materials"] = [get_material_info(mat) for mat in bpy.data.materials]
        
    scene_info["collections"] = [{"name": col.name, "objects": [obj.name for obj in col.objects]} 
                                 for col in bpy.data.collections]
    
    return scene_info

@dataclass
class Cmd_BlenderDumpSceneInformation(CommandBase):
    label = "Sample - Blender: Dump Scene Information"
    tooltip = "Dump Blender scene information to a JSON file"

    ui_class = "CmdUI_FileCollector"

    param_output_type: str = field(
        default="all",
        metadata={
            "help": "Type of information to dump",
            "items": [
                "all",
                "objects",
                "materials",
                "textures",
                "cameras",
                "lights",
                "collections"
            ],
        }
    )

    def run(self, data={}):
        """Run the command to dump Blender scene information"""
        target_files = data["target_files"]

        for target_file in target_files:
            logger.info("process: {0}".format(target_file))

            output_path = Path('E:/Temp/') / f"{Path(target_file).stem}_info.json"
            # Get scene information
            scene_info = get_scene_info()
            
            # Save to JSON
            with open(output_path, 'w') as f:
                json.dump(scene_info, f, indent=4)
