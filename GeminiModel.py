import sys
import os
import bpy

# 1. Ensure Blender sees our installed module
user_modules = os.path.join(bpy.utils.user_resource('SCRIPTS'), "modules")
if user_modules not in sys.path:
    sys.path.append(user_modules)

from google import genai

# 2. Setup Client (Replace with your key from AI Studio)
client = genai.Client(api_key="AIzaSyDbSWGXB6cEiQ4AxBMpofGTcXctm0D9dlI")

# 3. Call the latest model
response = client.models.generate_content(
    model="gemini-3-pro-preview", 
    contents="Write a Blender Python script to create a spiral of spheres."
)

print("-" * 30)
print("GEMINI RESPONSE:")
print(response.text)
print("-" * 30)