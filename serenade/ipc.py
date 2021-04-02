import asyncio
import iterm2
import json
import uuid
import websockets


DEBUG = False


def log(*args):
    if DEBUG:
        print("IPC:", *args)


class Ipc:
    def __init__(self, command_handler):
        self.command_handler = command_handler
        self.websocket = None

        self.app = "iterm"
        self.plugin_id = str(uuid.uuid4())
        self.active_message = {
            "app": self.app,
            "id": self.plugin_id
        }
        self.url = "ws://localhost:17373/"

        self.heartbeat_task = asyncio.create_task(self.heartbeat())

    async def retry_connection(self):
        while True:
            # Reset the active/heartbeat message with a new UUID
            self.plugin_id = str(uuid.uuid4())
            self.active_message = {
                "app": self.app,
                "id": self.plugin_id
            }
            try:
                await self.connect()
            except (OSError, websockets.exceptions.ConnectionClosedError):
                self.websocket = None
                log("Could not connect")
                await asyncio.sleep(1)
                log("Retrying ...")

    async def focus_listener(self, connection, session_id):
        async with iterm2.FocusMonitor(connection) as mon:
            while True:
                update = await mon.async_get_next_update()
                if update.active_session_changed and update.active_session_changed.session_id == session_id:
                    await self.send("active", self.active_message)
                    log("Sent active message", self.active_message)

    async def connect(self):
        async with websockets.connect(self.url) as websocket:
            self.websocket = websocket
            log("Connected, websocket")

            await self.send("active", self.active_message)
            log("Sent active message", self.active_message)

            await self.message_handler()

    async def heartbeat(self):
        while True:
            await self.send("heartbeat", self.active_message)
            await asyncio.sleep(60)

    async def send(self, message, data):
        if self.websocket:
            log("Sending raw message:")
            log(message, data)
            await self.websocket.send(json.dumps({
                "message": message,
                "data": data
            }))

    async def message_handler(self):
        async for message in self.websocket:
            try:
                data = json.loads(message).get("data")
                if not data:
                    continue
            except json.JSONDecodeError:
                continue

            callback = data.get("callback")
            result = await self.command_handler.handle(data.get("response"))

            await self.send("callback", {
                "callback": callback,
                "data": result
            })
            log("Received raw message:")
            log(message)
