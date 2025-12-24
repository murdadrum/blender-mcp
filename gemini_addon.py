import bpy
import os
import sys
import subprocess
import site

# --- ADDON METADATA ---
bl_info = {
    "name": "Gemini 3 Blender Assistant",
    "author": "Murdadrum",
    "version": (1, 4, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Gemini MCP",
    "description": "Integrated Gemini 3 AI for modeling and scripting",
    "category": "Development",
}

# --- UTILS ---

def get_dependencies_status():
    """Checks if required packages are installed."""
    try:
        import google.genai
        import dotenv
        return True
    except ImportError:
        return False

def install_dependencies():
    """Installs google-genai and python-dotenv to the user scripts modules."""
    python_exe = sys.executable
    target = os.path.join(bpy.utils.user_resource('SCRIPTS'), "modules")
    
    # Ensure target directory exists
    if not os.path.exists(target):
        os.makedirs(target)

    # Install using pip
    subprocess.check_call([python_exe, "-m", "pip", "install", "google-genai", "python-dotenv", "--target", target])

def setup_environment():
    """Initializes paths and loads environment variables."""
    # 1. Add custom modules folder to sys.path
    user_modules = os.path.join(bpy.utils.user_resource('SCRIPTS'), "modules")
    if user_modules not in sys.path:
        sys.path.append(user_modules)

    # 2. Add local 'src' directory
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    src_path = os.path.join(addon_dir, "src")
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.append(src_path)

    # 3. Load .env
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(addon_dir, ".env")
        load_dotenv(env_path)
    except ImportError:
        pass # Dependencies might not be installed yet

def _manual_env_parse(env_path):
    """Fallback: Manually parses .env file if dotenv fails."""
    if not os.path.exists(env_path):
        return {}
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    except Exception as e:
        print(f"Manual env parse failed: {e}")
    return env_vars

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
            ('gemini-3-flash-preview', "Gemini 3 Flash", "Fast reasoning"),
            ('gemini-3-pro-preview', "Gemini 3 Pro", "Deep complex logic"),
        ],
        default='gemini-3-flash-preview'
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

class OBJECT_OT_GeminiInstallDeps(bpy.types.Operator):
    bl_idname = "object.gemini_install_deps"
    bl_label = "Install Dependencies"
    bl_description = "Installs google-genai and python-dotenv"

    def execute(self, context):
        try:
            install_dependencies()
            setup_environment()
            self.report({'INFO'}, "Dependencies installed successfully!")
        except Exception as e:
            self.report({'ERROR'}, f"Installation failed: {str(e)}")
            return {'CANCELLED'}
        return {'FINISHED'}

class OBJECT_OT_GeminiTestConnection(bpy.types.Operator):
    bl_idname = "object.gemini_test_connection"
    bl_label = "Test Connection"
    
    def execute(self, context):
        setup_environment()
        try:
            from google import genai
            from dotenv import load_dotenv
            
            settings = context.scene.gemini_tools
            addon_dir = os.path.dirname(os.path.realpath(__file__))
            env_path = os.path.join(addon_dir, ".env")
            load_dotenv(env_path)
            
            api_key = os.getenv("GEMINI_API_KEY")
            
            # Fallback to manual parsing if load_dotenv fails
            if not api_key:
                env_vars = _manual_env_parse(env_path)
                api_key = env_vars.get("GEMINI_API_KEY")
            
            # Finally check settings
            api_key = api_key or settings.api_key
            
            if not api_key:
                self.report({'ERROR'}, "Missing API Key")
                return {'CANCELLED'}

            client = genai.Client(api_key=api_key)
            client.models.generate_content(model=settings.model_name, contents="ping")
            
            settings.connection_status = 'SUCCESS'
            self.report({'INFO'}, "Gemini: Connection Successful!")
        except ImportError:
            self.report({'ERROR'}, "Dependencies missing. Please install them first.")
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
            from dotenv import load_dotenv
            
            settings = context.scene.gemini_tools
            addon_dir = os.path.dirname(os.path.realpath(__file__))
            env_path = os.path.join(addon_dir, ".env")
            load_dotenv(env_path)
            
            api_key = os.getenv("GEMINI_API_KEY")
            
            # Fallback to manual parsing
            if not api_key:
                env_vars = _manual_env_parse(env_path)
                api_key = env_vars.get("GEMINI_API_KEY")

            api_key = api_key or settings.api_key
            
            if not api_key:
                self.report({'ERROR'}, "Missing API Key")
                return {'CANCELLED'}

            client = genai.Client(api_key=api_key)
            full_prompt = (
                "You are a Blender Python expert. Output ONLY raw executable code. "
                "No markdown, no conversation. Task: " + settings.prompt_input
            )
            
            response = client.models.generate_content(model=settings.model_name, contents=full_prompt)
            raw_code = response.text.replace("```python", "").replace("```", "").strip()
            
            exec(raw_code, globals())
            self.report({'INFO'}, "Gemini: Script executed successfully.")
            
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
        if not hasattr(context.scene, "gemini_tools"):
            return
            
        settings = context.scene.gemini_tools
        
        # Dependency check
        if not get_dependencies_status():
            layout.alert = True
            layout.operator("object.gemini_install_deps", icon='IMPORT', text="Install Dependencies")
            layout.label(text="Dependencies missing (google-genai, dotenv)")
            return

        # Normal UI
        status = settings.connection_status
        col = layout.column(align=True)
        
        row = col.row(align=True)
        if status == 'SUCCESS':
            row.operator("object.gemini_test_connection", icon='CHECKMARK', text="Connected")
        elif status == 'FAILED':
            row.alert = True
            row.operator("object.gemini_test_connection", icon='ERROR', text="Retry Connection")
        else:
            row.operator("object.gemini_test_connection", icon='WORLD', text="Test Connection")

        layout.separator()
        
        box = layout.box()
        box.prop(settings, "model_name")
        box.prop(settings, "prompt_input", text="")
        
        layout.operator("object.gemini_execute", icon='PLAY', text="Generate & Run")

# --- REGISTRATION ---
classes = (
    GeminiSettings,
    OBJECT_OT_GeminiInstallDeps,
    OBJECT_OT_GeminiTestConnection,
    OBJECT_OT_GeminiExecute,
    VIEW3D_PT_GeminiPanel,
)

def register():
    # Setup environment on registration (adds paths)
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
