import bpy
import os
import sys

# --- ADDON METADATA ---
bl_info = {
    "name": "Gemini 3 Blender Assistant",
    "author": "AI Thought Partner",
    "version": (1, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Gemini MCP",
    "description": "Direct Gemini 3 API integration",
    "category": "Development",
}

# --- SAFE DEPENDENCY LOADING ---
def try_load_dotenv():
    try:
        from dotenv import load_dotenv, find_dotenv
        load_dotenv(find_dotenv())
        return True
    except ImportError:
        return False

# --- PROPERTIES ---
class GeminiSettings(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="API Key",
        subtype='PASSWORD'
    )
    prompt_input: bpy.props.StringProperty(
        name="Prompt",
        default="Add a torus with a gold material"
    )
    model_name: bpy.props.EnumProperty(
        name="Model",
        items=[
            ('gemini-3-flash', "Gemini 3 Flash", ""),
            ('gemini-3-pro-preview', "Gemini 3 Pro", ""),
        ],
        default='gemini-3-flash'
    )
    connection_status: bpy.props.EnumProperty(
        items=[('NONE', "Not Tested", ""), ('SUCCESS', "Success", ""), ('FAILED', "Failed", "")],
        default='NONE'
    )

# --- OPERATORS ---
class OBJECT_OT_GeminiExecute(bpy.types.Operator):
    bl_idname = "object.gemini_execute"
    bl_label = "Generate & Run"
    
    def execute(self, context):
        # Ensure dependencies are available before running
        if not try_load_dotenv():
            self.report({'ERROR'}, "Missing 'python-dotenv'. Install via terminal.")
            return {'CANCELLED'}
            
        settings = context.scene.gemini_tools
        # Logic to call Gemini goes here...
        self.report({'INFO'}, "Attempting to execute...")
        return {'FINISHED'}

# --- UI PANEL ---
class VIEW3D_PT_GeminiPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gemini MCP'
    bl_label = 'Gemini 3 AI Assistant'

    def draw(self, context):
        layout = self.layout
        # Ensure properties are accessed correctly to avoid blank panel
        if not hasattr(context.scene, "gemini_tools"):
            layout.label(text="Error: Settings not initialized.")
            return

        settings = context.scene.gemini_tools
        
        col = layout.column(align=True)
        
        # Check for dotenv status in UI
        if not try_load_dotenv():
            col.alert = True
            col.label(text="Missing Library: python-dotenv", icon='ERROR')
        
        col.prop(settings, "api_key", icon='KEY')
        col.prop(settings, "model_name")
        
        layout.separator()
        
        box = layout.box()
        box.prop(settings, "prompt_input", text="")
        
        layout.operator("object.gemini_execute", icon='PLAY')

# --- REGISTRATION ---
classes = (GeminiSettings, OBJECT_OT_GeminiExecute, VIEW3D_PT_GeminiPanel)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gemini_tools = bpy.props.PointerProperty(type=GeminiSettings)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gemini_tools

if __name__ == "__main__":
    register()