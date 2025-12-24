import os

# Mimic the logic in gemini_addon.py
addon_dir = os.path.dirname(os.path.realpath(__file__))
env_path = os.path.join(addon_dir, ".env")

print(f"Script location: {os.path.realpath(__file__)}")
print(f"Addon Directory: {addon_dir}")
print(f"Expected .env path: {env_path}")
print(f"Does .env exist? {os.path.exists(env_path)}")

if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"Loaded .env. GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')}")
    except ImportError:
        print("dotenv not installed")
