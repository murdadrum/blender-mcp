import bpy
import os
import sys
import subprocess
import site

# --- ADDON METADATA ---
bl_info = {
    "name": "Gemini 3 Blender Assistant",
    "author": "murdadrum",
    "version": (1, 5, 0),
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
        import sounddevice
        import numpy
        import scipy.io.wavfile
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
    subprocess.check_call([python_exe, "-m", "pip", "install", "google-genai", "python-dotenv", "sounddevice", "numpy", "scipy", "--target", target])

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
class GEMINI_MCP_ChatLine(bpy.types.PropertyGroup):
    role: bpy.props.EnumProperty(
        items=[('user', "User", ""), ('ai', "AI", "")]
    )
    content: bpy.props.StringProperty()

class GEMINI_MCP_Settings(bpy.types.PropertyGroup):
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
    is_recording: bpy.props.BoolProperty(
        name="Is Recording",
        default=False
    )
    chat_history: bpy.props.CollectionProperty(type=GEMINI_MCP_ChatLine)

# --- OPERATORS ---

class GEMINI_MCP_OT_InstallDeps(bpy.types.Operator):
    bl_idname = "gemini_mcp.install_deps"
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

class GEMINI_MCP_OT_TestConnection(bpy.types.Operator):
    bl_idname = "gemini_mcp.test_connection"
    bl_label = "Test Connection"
    
    def execute(self, context):
        setup_environment()
        try:
            from google import genai
            from dotenv import load_dotenv
            
            settings = context.scene.gemini_mcp
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

class GEMINI_MCP_OT_Execute(bpy.types.Operator):
    bl_idname = "gemini_mcp.execute"
    bl_label = "Generate & Run"
    
    def execute(self, context):
        setup_environment()
        try:
            from google import genai
            from dotenv import load_dotenv
            
            settings = context.scene.gemini_mcp
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
            
            # Update Chat History
            chat = settings.chat_history.add()
            chat.role = 'user'
            chat.content = settings.prompt_input
            
            chat = settings.chat_history.add()
            chat.role = 'ai'
            chat.content = "Executed command: " + settings.prompt_input
            
            self.report({'INFO'}, "Gemini: Script executed successfully.")
            
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            
        return {'FINISHED'}

class GEMINI_MCP_OT_VoiceRecord(bpy.types.Operator):
    bl_idname = "gemini_mcp.voice_record"
    bl_label = "Voice Command"
    bl_description = "Record a voice command for Gemini"
    
    _timer = None
    _recording = []
    _sample_rate = 44100
    _temp_wav = ""

    def modal(self, context, event):
        settings = context.scene.gemini_mcp
        
        if event.type == 'TIMER':
            if not settings.is_recording:
                return self.stop_recording(context)
            
        return {'PASS_THROUGH'}

    def execute(self, context):
        setup_environment()
        settings = context.scene.gemini_mcp
        
        if settings.is_recording:
            # Already recording, stop it
            settings.is_recording = False
            return {'FINISHED'}
        
        try:
            import sounddevice as sd
            import numpy as np
            import tempfile
            
            # Start recording
            settings.is_recording = True
            self._recording = []
            
            def callback(indata, frames, time, status):
                if status:
                    print(status)
                if settings.is_recording:
                    self._recording.append(indata.copy())
            
            self.stream = sd.InputStream(samplerate=self._sample_rate, channels=1, callback=callback)
            self.stream.start()
            
            # Register timer for modal
            wm = context.window_manager
            self._timer = wm.event_timer_add(0.1, window=context.window)
            wm.modal_handler_add(self)
            
            self.report({'INFO'}, "Recording started...")
            return {'RUNNING_MODAL'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Recording failed: {str(e)}")
            settings.is_recording = False
            return {'CANCELLED'}

    def stop_recording(self, context):
        import numpy as np
        import scipy.io.wavfile as wav
        import tempfile
        from google import genai
        from dotenv import load_dotenv

        settings = context.scene.gemini_mcp
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        
        self.stream.stop()
        self.stream.close()
        
        if not self._recording:
            self.report({'WARNING'}, "No audio recorded.")
            return {'FINISHED'}
            
        # Process audio
        audio_data = np.concatenate(self._recording, axis=0)
        temp_dir = tempfile.gettempdir()
        self._temp_wav = os.path.join(temp_dir, "gemini_voice_command.wav")
        wav.write(self._temp_wav, self._sample_rate, audio_data)
        
        self.report({'INFO'}, "Processing voice command...")
        
        # Call Gemini
        try:
            addon_dir = os.path.dirname(os.path.realpath(__file__))
            env_path = os.path.join(addon_dir, ".env")
            load_dotenv(env_path)
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                env_vars = _manual_env_parse(env_path)
                api_key = env_vars.get("GEMINI_API_KEY")
            api_key = api_key or settings.api_key
            
            if not api_key:
                self.report({'ERROR'}, "Missing API Key")
                return {'FINISHED'}

            client = genai.Client(api_key=api_key)
            
            # Load audio file
            with open(self._temp_wav, 'rb') as f:
                audio_bytes = f.read()

            full_prompt = (
                "You are a Blender Python expert. The user has provided a voice command. "
                "Output ONLY raw executable code. No markdown, no conversation."
            )
            
            from google.genai import types
            
            # Use Part.from_bytes for the new google-genai SDK
            audio_part = types.Part.from_bytes(
                data=audio_bytes,
                mime_type="audio/wav"
            )

            response = client.models.generate_content(
                model=settings.model_name,
                contents=[
                    full_prompt,
                    audio_part
                ]
            )
            
            raw_code = response.text.replace("```python", "").replace("```", "").strip()
            
            if raw_code:
                exec(raw_code, globals())
                
                # Update Chat History
                chat = settings.chat_history.add()
                chat.role = 'user'
                chat.content = "[Voice Command]"
                
                chat = settings.chat_history.add()
                chat.role = 'ai'
                chat.content = "Executed voice command."
                
                self.report({'INFO'}, "Gemini: Voice command executed.")
            else:
                self.report({'WARNING'}, "Gemini did not return any code.")
                
        except Exception as e:
            self.report({'ERROR'}, f"Processing failed: {str(e)}")
        finally:
            if os.path.exists(self._temp_wav):
                os.remove(self._temp_wav)
                
        return {'FINISHED'}

# --- UI PANEL ---
class GEMINI_MCP_PT_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gemini MCP'
    bl_label = 'Gemini 3 AI Assistant'

    def draw(self, context):
        layout = self.layout
        if not hasattr(context.scene, "gemini_mcp"):
            return
            
        settings = context.scene.gemini_mcp
        
        # Dependency check
        if not get_dependencies_status():
            layout.alert = True
            layout.operator("gemini_mcp.install_deps", icon='IMPORT', text="Install Dependencies")
            layout.label(text="Dependencies missing (google-genai, sounddevice, etc.)")
            return

        # Chat History Display
        if len(settings.chat_history) > 0:
            box = layout.box()
            for msg in settings.chat_history[-5:]: # Show last 5
                row = box.row()
                if msg.role == 'user':
                    row.label(text="YOU:", icon='USER')
                else:
                    row.label(text="AI:", icon='BLENDER')
                row.label(text=msg.content)
        
        layout.separator()
        
        # Config Box
        box = layout.box()
        box.prop(settings, "api_key", text="API Key")
        box.prop(settings, "model_name", text="Model")
        
        # Prompt Area
        layout.prop(settings, "prompt_input", text="")
        
        # Voice & Execute Buttons
        row = layout.row(align=True)
        row.scale_y = 1.2
        if settings.is_recording:
            row.operator("gemini_mcp.voice_record", icon='REC', text="Recording...")
        else:
            row.operator("gemini_mcp.voice_record", icon='SOUND', text="Voice")
            
        row.operator("gemini_mcp.execute", icon='PLAY', text="Run Text")

# --- REGISTRATION ---
classes = (
    GEMINI_MCP_ChatLine,
    GEMINI_MCP_Settings,
    GEMINI_MCP_OT_InstallDeps,
    GEMINI_MCP_OT_TestConnection,
    GEMINI_MCP_OT_Execute,
    GEMINI_MCP_OT_VoiceRecord,
    GEMINI_MCP_PT_Panel,
)

def register():
    # Setup environment on registration (adds paths)
    setup_environment()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gemini_mcp = bpy.props.PointerProperty(type=GEMINI_MCP_Settings)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.gemini_mcp

if __name__ == "__main__":
    register()
