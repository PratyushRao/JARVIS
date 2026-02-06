import os
import webbrowser
import pyautogui
import subprocess


def resolve_path(path):
    if "%DESKTOP%" in path:
        path = path.replace("%DESKTOP%", os.path.join(os.path.expanduser("~"), "Desktop"))
    return os.path.expandvars(os.path.expanduser(path))



def open_application(app):
    apps = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "task_manager": "taskmgr.exe",
        "control_panel": "control.exe",
        "settings": "ms-settings:",
        "file_explorer": "explorer.exe",
        "snipping_tool": "snippingtool.exe",
        "character_map": "charmap.exe",
        "on_screen_keyboard": "osk.exe",
        "magnifier": "magnify.exe",

        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "firefox": "firefox.exe",
        "brave": "brave.exe",
        "opera": "opera.exe",

        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "outlook": "outlook.exe",
        "onenote": "onenote.exe",

        "vscode": "Code.exe",
        "pycharm": "pycharm64.exe",
        "intellij": "idea64.exe",
        "git_bash": "git-bash.exe",

        "spotify": "spotify.exe",
        "vlc": "vlc.exe",
        "windows_media_player": "wmplayer.exe",

        "discord": "discord.exe",
        "teams": "ms-teams.exe",
        "zoom": "zoom.exe",
        "skype": "skype.exe",

        "steam": "steam.exe",
        "obs": "obs64.exe",
        "virtualbox": "VirtualBox.exe",
        "docker_desktop": "Docker Desktop.exe",
    }


    exe = apps.get(app.lower())
    if not exe:
        return "App not allowed ❌"

    try:
        subprocess.Popen([exe])
        return f"{app} opened ✅"
    except Exception as e:
        return f"Failed to open {app}: {e}"


def close_application(app):
    try:
        subprocess.run(f"taskkill /IM {app}.exe /F", shell=True)
        return f"{app} closed 🛑"
    except Exception as e:
        return f"Failed to close {app}: {e}"


def open_website(url):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url} 🌐"


def close_website(browser="chrome"):
    browsers = {
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "firefox": "firefox.exe"
    }

    exe = browsers.get(browser.lower())
    if not exe:
        return "Unsupported browser"

    subprocess.run(f"taskkill /IM {exe} /F", shell=True)
    return f"{browser} closed 🌐🛑"



def set_volume(level):
    try:
        level = max(0, min(100, int(level)))
        pyautogui.press("volumedown", presses=50)
        pyautogui.press("volumeup", presses=int(level / 2))
        return f"Volume set to {level}% 🔊"
    except Exception as e:
        return f"Volume control failed: {e}"



def create_folder(path):
    try:
        path = resolve_path(path)
        os.makedirs(path, exist_ok=True)
        return f"Folder created at {path} ✅"
    except Exception as e:
        return f"Failed to create folder: {e}"



def delete_file(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
            return f"Deleted file: {path} 🗑"
        return "File not found"
    except Exception as e:
        return f"Delete failed: {e}"



def run_executable(path, args=""):
    try:
        if not path.lower().endswith(".exe"):
            return "Only .exe files allowed"

        if not os.path.exists(path):
            return "Executable not found"

        subprocess.Popen(f'"{path}" {args}', shell=True)
        return f"Running {os.path.basename(path)} ▶"
    except Exception as e:
        return f"Execution failed: {e}"
