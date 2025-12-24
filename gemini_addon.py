import bpy
import os
import sys

# --- ADDON METADATA ---
bl_info = {
    "name": "Gemini 3 Blender Assistant",
    "author": "Murdadrum",
    "version": (1, 3, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Gemini MCP",
    "description": "Integrated Gemini 3 AI for 3D modeling and script generation",
    "category": "Development",
}

# --- ENVIRONMENT & DEPENDENCY SETUP ---
def setup_environment():
    """Initializes paths and loads environment variables from the local git repo."""
    # 1. Add custom modules folder to sys.path
    user_modules = os.path.join(bpy.utils.user_resource('SCRIPTS'), "modules")
    if user_modules not in sys.path:
        sys.path.append(user_modules)

    # 2. Add local 'src' directory from your git repo
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    src_path = os.path.join(addon_dir, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.append(src_path)

    # 3. Safely load .env file
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(addon_dir, ".env")
        load_dotenv(env_path)
        return True
    except ImportError:
        return False

# --- PROPERTIES ---
class GeminiSettings(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Google AI Studio Key (Leave blank if set in .env)",
        subtype='PASSWORD'
    )
    prompt_input: bpy.props.StringProperty(
        name="Prompt",
        description="Task for Gemini to perform",
        default="Create a procedural crystal formation"
    )
    model_name: bpy.props.EnumProperty(
        name="Model",
        items=[
            ('gemini-3-flash', "Gemini 3 Flash", "Fast reasoning"),
            ('gemini-3-pro-preview', "Gemini 3 Pro", "Deep complex logic"),
        ],
        default='gemini-3-flash'
    )
    connection_status: bpy.props.EnumProperty(
        items=[
            ('NONE', "Not Tested", ""),
            ('SUCCESS', "Connected", ""),
            ('FAILED', "Connection Error", "")
        ],
        default='NONE'
    )

# --- OPERATORS ---
class OBJECT_OT_GeminiTestConnection(bpy.types.Operator):
    bl_idname = "object.gemini_test_connection"
    bl_label = "Test Connection"
    
    def execute(self, context):
        setup_environment()
        try:
            from google import genai
            settings = context.scene.gemini_tools
            key = os.getenv("GEMINI_API_KEY") or settings.api_key
            
            client = genai.Client(api_key=key)
            # Connectivity ping
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
        try:
            from google import genai
            settings = context.scene.gemini_tools
            key = os.getenv("GEMINI_API_KEY") or settings.api_key
            
            if not key:
                self.report({'ERROR'}, "API Key missing! Check .env or settings.")
                return {'CANCELLED'}

            client = genai.Client(api_key=key)
            full_prompt = (
                "You are a Blender Python expert. Output ONLY raw executable code. "
                "No markdown, no conversation. Task: " + settings.prompt_input
            )
            
            response = client.models.generate_content(model=settings.model_name, contents=full_prompt)
            raw_code = response.text.replace("```python", "").replace("```", "").strip()
            
            # Execute in global scope
            exec(raw_code, globals())
            self.report({'INFO'}, "Gemini: Script executed successfully.")
            
        except Exception as e:
            self.report({'ERROR'}, f"API Error: {str(e)}")
            
        return {'FINISHED'}

# --- UI PANEL ---
class VIEW3D_PT_GeminiPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gemini MCP'
    bl_label = 'Gemini 3 AI Assistant'

    def draw(self, context):
        layout = self.layout
        if not hasattr(context.scene, "gemini_tools"):
            return
            
        settings = context.scene.gemini_tools
        status = settings.connection_status

        col = layout.column(align=True)
        
        # Test Connection / Feedback
        row = col.row(align=True)
        if status == 'SUCCESS':
            row.operator("object.gemini_test_connection", icon='CHECKMARK', text="Connected")
        elif status == 'FAILED':
            row.alert = True
            row.operator("object.gemini_test_connection", icon='ERROR', text="Retry Connection")
        else:
            row.operator("object.gemini_test_connection", icon='WORLD', text="Test Connection")

        layout.separator()
        
        # Main Interface
        box = layout.box()
        box.prop(settings, "model_name")
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