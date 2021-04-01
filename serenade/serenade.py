#!/usr/bin/env python3
import asyncio
import iterm2
import traceback

from command_handler import CommandHandler
from ipc import Ipc


async def main(connection):
    while True:
        command_handler = CommandHandler(connection)
        ipc = Ipc(command_handler)
        ipc_task = asyncio.create_task(ipc.retry_connection())
        keyboard_listener_task = asyncio.create_task(command_handler.keyboard_listener())
        screen_listener_task = asyncio.create_task(command_handler.screen_listener())
        tasks = [ipc_task, keyboard_listener_task, screen_listener_task]
        try:
            print("Starting tasks")
            await asyncio.gather(*tasks)
        except Exception as e:
            print("Exception:", e)
            traceback.print_exc()
            for t in tasks:
                t.cancel()
            await asyncio.sleep(1)


# This instructs the script to run the "main" coroutine and to keep running even after it returns.
iterm2.run_forever(main)
