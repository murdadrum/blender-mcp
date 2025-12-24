import bpy
import os
import sys
import subprocess

# --- ADDON METADATA ---
bl_info = {
    "name": "Gemini 3 Blender Assistant",
    "author": "Murdadrum",
    "version": (1, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Gemini MCP",
    "description": "Direct Gemini 3 API integration for code generation",
    "category": "Development",
}

# --- DYNAMIC PATH HANDLING ---
def setup_environment():
    """Ensure Blender can find .env and local modules from the git repo."""
    # 1. Add 'modules' folder where you installed google-genai and python-dotenv
    user_modules = os.path.join(bpy.utils.user_resource('SCRIPTS'), "modules")
    if user_modules not in sys.path:
        sys.path.append(user_modules)

    # 2. Try to load .env from the git repo
    try:
        from dotenv import load_dotenv, find_dotenv
        # find_dotenv() searches up the directory tree for your .env file
        load_dotenv(find_dotenv())
        return True
    except ImportError:
        return False

# --- PROPERTIES ---
class GeminiSettings(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Google AI Studio API Key (Leave blank if using .env)",
        subtype='PASSWORD'
    )
    prompt_input: bpy.props.StringProperty(
        name="Prompt",
        description="What should the AI do?",
        default="Create a grid of 10x10 cubes"
    )
    model_name: bpy.props.EnumProperty(
        name="Model",
        items=[
            ('gemini-3-flash', "Gemini 3 Flash (Fast)", ""),
            ('gemini-3-pro-preview', "Gemini 3 Pro (Smart)", ""),
        ],
        default='gemini-3-flash'
    )
    connection_status: bpy.props.EnumProperty(
        items=[
            ('NONE', "Not Tested", ""),
            ('SUCCESS', "Connected", "Icon: CHECKMARK"),
            ('FAILED', "Failed", "Icon: ERROR")
        ],
        default='NONE'
    )

# --- OPERATORS ---
class OBJECT_OT_GeminiTestConnection(bpy.types.Operator):
    bl_idname = "object.gemini_test_connection"
    bl_label = "Test Gemini Connection"
    
    def execute(self, context):
        setup_environment()
        from google import genai
        settings = context.scene.gemini_tools
        
        # Priority: .env variable > UI Field
        key = os.getenv("GEMINI_API_KEY") or settings.api_key
        
        try:
            client = genai.Client(api_key=key)
            # Minimal 'ping' request
            client.models.generate_content(model="gemini-2.0-flash", contents="ping")
            settings.connection_status = 'SUCCESS'
            self.report({'INFO'}, "Gemini: Connection Successful!")
        except Exception as e:
            settings.connection_status = 'FAILED'
            self.report({'ERROR'}, f"Connection Failed: {str(e)}")
            
        return {'FINISHED'}

class OBJECT_OT_GeminiExecute(bpy.types.Operator):
    bl_idname = "object.gemini_execute"
    bl_label = "Generate & Run"
    
    def execute(self, context):
        setup_environment()
        from google import genai
        settings = context.scene.gemini_tools
        key = os.getenv("GEMINI_API_KEY") or settings.api_key
        
        if not key:
            self.report({'ERROR'}, "Missing API Key. Check your .env file.")
            return {'CANCELLED'}

        try:
            client = genai.Client(api_key=key)
            full_prompt = (
                "System: Output ONLY raw, executable Python code for Blender. "
                "No markdown, no explanations. "
                f"Task: {settings.prompt_input}"
            )
            
            response = client.models.generate_content(model=settings.model_name, contents=full_prompt)
            raw_code = response.text.replace("```python", "").replace("```", "").strip()
            
            # Execute generated code in the global scope
            exec(raw_code, globals())
            self.report({'INFO'}, "Gemini: Code Executed Successfully")
            
        except Exception as e:
            self.report({'ERROR'}, f"Execution Error: {str(e)}")
            
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
        
        # Connection Status / Test Button
        row = col.row(align=True)
        if status == 'SUCCESS':
            row.operator("object.gemini_test_connection", icon='CHECKMARK', text="Connected")
        elif status == 'FAILED':
            row.alert = True
            row.operator("object.gemini_test_connection", icon='ERROR', text="Retry Connection")
        else:
            row.operator("object.gemini_test_connection", icon='WORLD', text="Test Connection")

        layout.separator()
        
        # Model Selection & Prompt
        box = layout.box()
        box.prop(settings, "model_name", text="Model")
        box.prop(settings, "prompt_input", text="")
        
        layout.operator("object.gemini_execute", icon='PLAY', text="Generate & Run")

# --- REGISTRATION ---
classes = (
    GeminiSettings,
    OBJECT_OT_GeminiTestConnection,
    OBJECT_OT_GeminiExecute,
    VIEW3D_PT_GeminiPanel,
)

def register():
    # Attempt environment setup during registration
    setup_environment()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gemini_tools = bpy.props.PointerProperty(type=GeminiSettings)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gemini_tools

if __name__ == "__main__":
    register()