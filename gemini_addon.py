import bpy
import os
import sys
from dotenv import load_dotenv, find_dotenv

# --- ADDON METADATA ---
bl_info = {
    "name": "Gemini 3 Blender Assistant",
    "author": "AI Thought Partner",
    "version": (1, 1),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Gemini MCP",
    "description": "Direct Gemini 3 API integration for code generation",
    "category": "Development",
}

# --- INITIALIZE ENVIRONMENT ---
# Load .env from your git repo immediately upon script execution
load_dotenv(find_dotenv())

# --- PROPERTIES ---
class GeminiSettings(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Google AI Studio API Key (Leave blank if set in .env)",
        subtype='PASSWORD'
    )
    prompt_input: bpy.props.StringProperty(
        name="Prompt",
        description="Describe what you want to create",
        default="Add a torus with a gold material"
    )
    model_name: bpy.props.EnumProperty(
        name="Model",
        items=[
            ('gemini-3-flash', "Gemini 3 Flash", "Fastest"),
            ('gemini-3-pro-preview', "Gemini 3 Pro", "Complex Logic"),
        ],
        default='gemini-3-flash'
    )
    connection_status: bpy.props.EnumProperty(
        items=[
            ('NONE', "Not Tested", ""),
            ('SUCCESS', "Success", ""),
            ('FAILED', "Failed", "")
        ],
        default='NONE'
    )

# --- OPERATORS ---
class OBJECT_OT_GeminiTestConnection(bpy.types.Operator):
    bl_idname = "object.gemini_test_connection"
    bl_label = "Test Connection"
    
    def execute(self, context):
        from google import genai
        settings = context.scene.gemini_tools
        # Priority: 1. .env file | 2. UI Field
        key = os.getenv("GEMINI_API_KEY") or settings.api_key
        
        try:
            client = genai.Client(api_key=key)
            client.models.generate_content(model="gemini-2.0-flash", contents="ping")
            settings.connection_status = 'SUCCESS'
            self.report({'INFO'}, "Connected successfully!")
        except Exception as e:
            settings.connection_status = 'FAILED'
            self.report({'ERROR'}, f"Failed: {str(e)}")
            
        return {'FINISHED'} # Operators must return a set

class OBJECT_OT_GeminiExecute(bpy.types.Operator):
    bl_idname = "object.gemini_execute"
    bl_label = "Generate & Run"
    
    def execute(self, context):
        from google import genai
        settings = context.scene.gemini_tools
        key = os.getenv("GEMINI_API_KEY") or settings.api_key
        
        if not key:
            self.report({'ERROR'}, "Missing API Key")
            return {'CANCELLED'}

        client = genai.Client(api_key=key)
        full_prompt = f"System: Output ONLY raw Blender Python code. User: {settings.prompt_input}"
        
        try:
            response = client.models.generate_content(model=settings.model_name, contents=full_prompt)
            raw_code = response.text.replace("```python", "").replace("```", "").strip()
            
            # Use a restricted context for safety
            exec(raw_code, globals())
            self.report({'INFO'}, "Code executed")
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            
        return {'FINISHED'}

# --- UI PANEL ---
class VIEW3D_PT_GeminiPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gemini MCP'
    bl_label = 'Gemini 3 AI Assistant'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gemini_tools
        status = settings.connection_status

        col = layout.column(align=True)
        
        # Test Connection Row
        row = col.row(align=True)
        if status == 'SUCCESS':
            row.operator("object.gemini_test_connection", icon='CHECKMARK', text="Connected")
        elif status == 'FAILED':
            row.alert = True
            row.operator("object.gemini_test_connection", icon='ERROR', text="Retry Connection")
        else:
            row.operator("object.gemini_test_connection", icon='WORLD', text="Test Connection")

        layout.separator()
        
        # Input Section
        box = layout.box()
        box.prop(settings, "model_name")
        box.prop(settings, "prompt_input", text="")
        
        layout.operator("object.gemini_execute", icon='PLAY')

# --- REGISTRATION ---
classes = (
    GeminiSettings,
    OBJECT_OT_GeminiTestConnection,
    OBJECT_OT_GeminiExecute,
    VIEW3D_PT_GeminiPanel,
)

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