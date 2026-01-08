from pathlib import Path

ENV_TEMPLATE = """STAFF_PASSWORD=change-me
SECRET_KEY=change-me-too
DEBUG=false
"""

if __name__ == "__main__":
    env_path = Path(".env")
    if env_path.exists():
        print(".env already exists")
    else:
        env_path.write_text(ENV_TEMPLATE)
        print("Created .env")
