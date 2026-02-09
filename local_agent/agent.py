import asyncio
import websockets
import json
import time
from os_controller import *

SERVER = "wss://YOUR-BACKEND.onrender.com/ws/agent"

LAST_ACTIVITY = time.time()


def handle_command(cmd):
    global LAST_ACTIVITY
    LAST_ACTIVITY = time.time()

    print("handle_command received:", cmd)
    action = cmd.get("action")

    try:
        if action == "open_app":
            return open_application(cmd["app"])

        elif action == "close_app":
            return close_application(cmd["app"])

        elif action == "open_website":
            return open_website(cmd["url"])

        elif action == "close_website":
            return close_website(cmd.get("browser", "chrome"))

        elif action == "set_volume":
            return set_volume(cmd["level"])

        elif action == "create_folder":
            return create_folder(cmd["path"])

        elif action == "delete_file":
            return delete_file(cmd["path"])

        elif action == "run_exe":
            return run_executable(cmd["path"], cmd.get("args", ""))

        else:
            return "Unknown command"

    except Exception as e:
        return f"Command error: {e}"


async def run_agent():
    while True:
        try:
            async with websockets.connect(SERVER) as ws:
                print("Connected to Jarvis 🤖")

                while True:
                    try:
                        msg = await ws.recv()
                        print("Received message:", msg)

                        cmd = json.loads(msg)
                        result = handle_command(cmd)

                        print("Command handled, result:", result)
                        await ws.send(json.dumps({"result": result}))

                    except Exception as e:
                        print("Error handling message:", e)

        except Exception as e:
            print("Agent connection error:", e)
            await asyncio.sleep(5)


asyncio.run(run_agent())
