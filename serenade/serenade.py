#!/usr/bin/env python3
import asyncio
import iterm2
import traceback

from command_handler import CommandHandler
from ipc import Ipc


async def main(connection):
    app = await iterm2.async_get_app(connection)

    async def start_tasks(session_id):
        while True:
            command_handler = CommandHandler(connection, session_id)
            ipc = Ipc(command_handler)
            ipc_task = asyncio.create_task(ipc.retry_connection())
            keyboard_listener_task = asyncio.create_task(command_handler.keyboard_listener())
            screen_listener_task = asyncio.create_task(command_handler.screen_listener())
            update_prompt_task = asyncio.create_task(command_handler.update_prompt())
            tasks = [ipc_task, keyboard_listener_task, screen_listener_task, update_prompt_task]
            try:
                print("Starting tasks")
                await asyncio.gather(*tasks)
            except Exception as e:
                print("Exception:", e)
                traceback.print_exc()
                for t in tasks:
                    t.cancel()
                await asyncio.sleep(1)

    await (iterm2.EachSessionOnceMonitor.async_foreach_session_create_task(app, start_tasks))


# This instructs the script to run the "main" coroutine and to keep running even after it returns.
iterm2.run_forever(main)
