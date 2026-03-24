import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    basedir = getattr(sys, '_MEIPASS', os.getcwd())
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Ensure current directory is in sys.path
    sys.path.append(os.getcwd())
    
    # Path to app.py
    app_path = resolve_path("app.py")
    
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port=8501",
        "--server.headless=true",
    ]
    
    sys.exit(stcli.main())
