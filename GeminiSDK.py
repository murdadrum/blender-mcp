import sys
import subprocess
import os
import bpy

# Get the path to Blender's internal Python
python_exe = sys.executable

# Target the user-specific 'scripts/modules' folder (safe from permission errors)
user_script_path = bpy.utils.user_resource('SCRIPTS')
target_path = os.path.join(user_script_path, "modules")

if not os.path.exists(target_path):
    os.makedirs(target_path)

print(f"Installing Gemini SDK to: {target_path}")

try:
    # Use the new 'google-genai' library for Gemini 3+ support
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "google-genai", "--target", target_path], check=True)
    print("SUCCESS: Gemini SDK installed. Please RESTART Blender.")
except Exception as e:
    print(f"ERROR: {e}")