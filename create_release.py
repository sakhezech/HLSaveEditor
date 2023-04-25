import os
import PyInstaller.__main__

if __name__ == "__main__":
    PyInstaller.__main__.run([
        "savemanager.py", "-w", "--collect-data", "glfw", "-F", "-n", "HLSaveManager", "-i", os.path.join('res', 'icon.ico'), "--add-data", f"{os.path.join('res', 'icon.ico')}{os.pathsep}res/."
    ])
