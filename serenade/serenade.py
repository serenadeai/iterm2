#!/usr/bin/env python3
import asyncio
import iterm2
import traceback

from command_handler import CommandHandler
from ipc import Ipc


async def main(connection):
    app = await iterm2.async_get_app(connection)

    async def start_session_tasks(session_id):
        while True:
            session = app.get_session_by_id(session_id)
            command_handler = CommandHandler(connection, session_id, session)
            ipc = Ipc(command_handler)
            ipc_task = asyncio.create_task(ipc.retry_connection())
            keyboard_listener_task = asyncio.create_task(command_handler.keyboard_listener())
            screen_listener_task = asyncio.create_task(command_handler.screen_listener())
            focus_listener_task = asyncio.create_task(ipc.focus_listener(connection, session_id))
            update_prompt_task = asyncio.create_task(command_handler.update_prompt())
            tasks = [ipc_task, keyboard_listener_task, screen_listener_task, update_prompt_task, focus_listener_task]
            try:
                print("***", "Starting tasks for session", session_id)
                await asyncio.gather(*tasks)
            except Exception as e:
                print("Exception:", e)
                traceback.print_exc()
                for t in tasks:
                    t.cancel()
                await asyncio.sleep(1)

    await (iterm2.EachSessionOnceMonitor.async_foreach_session_create_task(app, start_session_tasks))


# This instructs the script to run the "main" coroutine and to keep running even after it returns.
iterm2.run_forever(main)
