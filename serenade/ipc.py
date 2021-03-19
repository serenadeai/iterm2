import asyncio
import json
import uuid
import websockets


class Ipc:
    def __init__(self, command_handler):
        self.command_handler = command_handler
        self.websocket = None

        app = "terminal"
        self.plugin_id = str(uuid.uuid4())
        self.active_message = {
            "app": app,
            "id": self.plugin_id
        }
        self.url = "ws://localhost:17373/"

        self.heartbeat_task = asyncio.create_task(self.heartbeat())

    async def retry_connection(self):
        try:
            await self.connect()
        except (OSError, websockets.exceptions.ConnectionClosedError):
            self.websocket = None
            # print("Could not connect")
            await asyncio.sleep(1)
            # print ("Retrying ...")
            await self.retry_connection()

    async def connect(self):
        async with websockets.connect(self.url) as websocket:
            self.websocket = websocket
            print(f"Connected {websocket}")

            await self.send("active", self.active_message)
            print("Sent active")

            await self.message_handler()

    async def heartbeat(self):
        while True:
            await self.send("heartbeat", self.active_message)
            await asyncio.sleep(60)

    async def send(self, message, data):
        if self.websocket:
            # print("Sending raw message:")
            # print(message)
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
            # print("Received raw message:")
            # print(message)
