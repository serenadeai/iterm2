#!/usr/bin/env python3
import asyncio
import iterm2

from command_handler import CommandHandler
from ipc import Ipc


async def main(connection):
    command_handler = CommandHandler(connection)
    ipc = Ipc(command_handler)
    asyncio.create_task(ipc.retry_connection())


# This instructs the script to run the "main" coroutine and to keep running even after it returns.
iterm2.run_forever(main)
