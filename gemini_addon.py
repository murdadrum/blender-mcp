import bpy
import sys
import subprocess
import os
from dotenv import load_dotenv, find_dotenv

# Find the .env file in your local git repo
# This works if addon.py is in the same folder as .env
load_dotenv(find_dotenv()) 

# Fallback check
api_key = os.getenv("GEMINI_API_KEY")

# --- ADDON METADATA ---
bl_info = {
    "name": "Gemini 3 Blender Assistant",
    "author": "AI Thought Partner",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Gemini MCP",
    "description": "Direct Gemini 3 API integration for code generation and execution",
    "category": "Development",
}

# --- DEPENDENCY MANAGEMENT ---
def ensure_dependencies():
    """Ensure google-genai is available in the path."""
    user_modules = os.path.join(bpy.utils.user_resource('SCRIPTS'), "modules")
    if user_modules not in sys.path:
        sys.path.append(user_modules)
    
    try:
        from google import genai
        return genai
    except ImportError:
        return None

# --- PROPERTIES ---
class GeminiSettings(bpy.types.PropertyGroup):
    api_key: bpy.props.StringProperty(
        name="API Key",
        description="Enter your Google AI Studio API Key",
        subtype='PASSWORD'
    )
    prompt_input: bpy.props.StringProperty(
        name="Prompt",
        description="Describe what you want to create or modify",
        default="Add a grid of 25 cubes with random heights"
    )
    model_name: bpy.props.EnumProperty(
        name="Model",
        items=[
            ('gemini-3-flash', "Gemini 3 Flash (Fast)", "Fastest and efficient"),
            ('gemini-3-pro-preview', "Gemini 3 Pro (Smart)", "Best for complex logic"),
        ],
        default='gemini-3-flash'
    )

# --- OPERATORS ---
class OBJECT_OT_GeminiExecute(bpy.types.Operator):
    bl_idname = "object.gemini_execute"
    bl_label = "Generate & Execute"
    bl_description = "Send prompt to Gemini and run the resulting Python code"
    
    def execute(self, context):
        genai = ensure_dependencies()
        if not genai:
            self.report({'ERROR'}, "Gemini SDK not found. Please install google-genai.")
            return {'CANCELLED'}
        
        settings = context.scene.gemini_tools
        if not settings.api_key:
            self.report({'ERROR'}, "Please enter an API Key first.")
            return {'CANCELLED'}

        client = genai.Client(api_key=settings.api_key)
        
        # System prompt to ensure we only get raw code
        full_prompt = (
            "System: You are a Blender Python expert. Output ONLY raw, valid Python code "
            "ready for Blender's exec() function. Do not include markdown formatting or explanations. "
            f"User Task: {settings.prompt_input}"
        )
        
        try:
            # Change the cursor to indicate processing
            wm = context.window_manager
            wm.progress_begin(0, 100)
            
            response = client.models.generate_content(
                model=settings.model_name,
                contents=full_prompt
            )
            
            # Clean formatting if the model still provides backticks
            raw_code = response.text.replace("```python", "").replace("```", "").strip()
            
            # Show the code in the system console for debugging
            print("\n--- GEMINI GENERATED CODE ---")
            print(raw_code)
            print("-----------------------------\n")
            
            # Execute the code in the global context
            exec(raw_code, globals())
            
            self.report({'INFO'}, f"Gemini: Success using {settings.model_name}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            print(f"Gemini Error Details: {e}")
        finally:
            wm.progress_end()
            
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
    
    # Check if API Key exists in .env or was entered manually
    env_key = os.getenv("GEMINI_API_KEY")
    
    col = layout.column(align=True)
    
    if env_key:
        row = col.row()
        row.label(text="API Key: Loaded from .env", icon='CHECKMARK')
    else:
        col.prop(settings, "api_key", icon='KEY')
        col.label(text="Tip: Set 'GEMINI_API_KEY' in your .env to skip this.", icon='INFO')

    col.prop(settings, "model_name", icon='NODE_COMPOSIT')
    
    layout.separator()
    
    box = layout.box()
    box.label(text="Prompt:")
    box.prop(settings, "prompt_input", text="")
    
    layout.operator("object.gemini_execute", icon='CONSOLE', text="Generate & Run")

# --- REGISTRATION ---
classes = (
    GeminiSettings,
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