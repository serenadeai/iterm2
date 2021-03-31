import asyncio
import iterm2

from build_command import build_command
from count_cursor import count_cursor

DEBUG = False


def log(*args):
    if DEBUG:
        print(*args)


class CommandHandler:
    def __init__(self, connection):
        self.connection = connection
        self.command_start_coords = None
        self.command_running = True
        self.source = ""
        self.cursor = 0
        self.undo_index = 0
        self.command_stack = []
        self.last_command_was_use = False
        asyncio.create_task(self.keyboard_listener())
        asyncio.create_task(self.screen_listener())

    async def keyboard_listener(self):
        async with iterm2.KeystrokeMonitor(self.connection) as mon:
            while True:
                keystroke = await mon.async_get()
                await self.check_keystroke(keystroke)

    async def screen_listener(self):
        app = await iterm2.async_get_app(self.connection)
        session = app.current_window.current_tab.current_session
        async with session.get_screen_streamer() as streamer:
            while True:
                await streamer.async_get()
                log("Screen output changed", self.command_running)
                if self.command_running:
                    log("Setting command start to cursor")
                    await self.set_coords()
                else:
                    await self.get_editor_state()

    async def handle(self, response):
        result = None

        # log(response)
        if response.get("execute"):
            for command in response.get("execute").get("commandsList"):
                command_type = command.get("type")

                if command_type == "COMMAND_TYPE_DIFF":
                    if self.last_command_was_use:
                        result = await self.diff(command, "use")
                        self.last_command_was_use = False
                    else:
                        result = await self.diff(command)
                if command_type == "COMMAND_TYPE_GET_EDITOR_STATE":
                    result = await self.get_editor_state()
                if command_type == "COMMAND_TYPE_UNDO":
                    result = await self.undo()
                    self.last_command_was_use = False
                if command_type == "COMMAND_TYPE_REDO":
                    result = await self.redo()
                    self.last_command_was_use = False
                if command_type == "COMMAND_TYPE_USE":
                    self.last_command_was_use = True
                    result = {
                        "message": "completed"
                    }

                # log(command)

        return result

    async def diff(self, data, command_type=""):
        # log("diff", data, command_type)
        if self.command_running:
            self.command_running = False
            await self.set_coords(keypress=False)

        source, cursor = await self.get_prompt_and_cursor()

        text = data.get("insertDiff", "")
        if text.endswith("\n"):
            text = text[:-1]

        delete = data.get("deleteEnd") is not None and \
                 data.get("deleteStart") is not None and \
                 data.get("deleteEnd") - data.get("deleteStart") != 0
        new_cursor = data.get("deleteEnd") if delete else \
            (cursor if text else data.get("cursor"))

        delete_count = data.get("deleteEnd", 0) - data.get("deleteStart", 0)
        cursor_adjustment = new_cursor - cursor

        # For undo commands, manually calculate the adjustments to the cursor, and deletes or inserts
        if command_type == "undo":
            delete_count = len(data.get("insertDiff", ""))
            if delete:
                cursor_adjustment = data.get("deleteStart", 0) - cursor + delete_count
            else:
                cursor_adjustment = data.get("prev_cursor") - cursor + delete_count
            text = data.get("deleted", "")
        # No action is needed for redo commands since the original command is passed in again
        elif command_type == "redo":
            pass
        # Otherwise, append the original command (with additional data about the current state) to the
        # command stack so we can undo it later
        else:
            data["prev_cursor"] = cursor
            if delete:
                # log("Deleting from", source, data.get("deleteStart"), data.get("deleteEnd"))
                data["deleted"] = source[data.get("deleteStart"):data.get("deleteEnd")]
            # If it's a use command, push this as the last valid command
            if command_type == "use":
                # Remember the original command's deleted text
                data["deleted"] = self.command_stack[self.undo_index - 1].get("deleted", "")
                if data["deleted"].endswith("\n"):
                    data["deleted"] = data["deleted"][:-1]
                self.command_stack = self.command_stack[0:self.undo_index - 1]
                self.undo_index -= 1
            # Otherwise, ensure it's the last command in the stack
            else:
                self.command_stack = self.command_stack[0:self.undo_index]
            self.command_stack.append(data)
            self.undo_index += 1

        # Don't delete anything if it's a use command, since the client will do it for us immediately.
        if command_type == "use":
            cursor_adjustment = 0
            delete_count = 0

        log("Adjusting cursor by", cursor_adjustment)
        log("Deleting by", delete_count)
        log("Inserting", text)

        return {
            "message": "applyDiff",
            "data": {
                "adjustCursor": cursor_adjustment,
                "deleteCount": delete_count,
                "text": text,
                # Tell the client to not automatically press backspace if this is an undo command.
                "skipBackspace": True,
            }
        }

    async def undo(self):
        self.undo_index -= 1
        if self.undo_index < 0:
            self.undo_index = 0
            return {}

        undo_command = self.command_stack[self.undo_index]
        result = await self.diff(undo_command, "undo")
        return result

    async def redo(self):
        self.undo_index += 1
        if self.undo_index > len(self.command_stack):
            self.undo_index = len(self.command_stack)
            return {}

        redo_command = self.command_stack[self.undo_index - 1]
        result = await self.diff(redo_command, "redo")
        return result

    async def get_prompt_and_cursor(self):
        app = await iterm2.async_get_app(self.connection)
        if app.current_window is None:
            return "", 0
        session = app.current_window.current_tab.current_session
        screen_contents = await session.async_get_screen_contents()
        line_info = await session.async_get_line_info()
        cursor_coord = screen_contents.cursor_coord
        command_start_coords = self.command_start_coords if self.command_start_coords else cursor_coord
        command = build_command(command_start_coords, screen_contents, line_info)
        cursor = count_cursor(command_start_coords, cursor_coord, session.grid_size.width)
        if cursor > len(command):
            return command, len(command)
        return command, cursor

    async def get_editor_state(self):
        source, cursor = await self.get_prompt_and_cursor()
        log("editorState:")
        log(source)
        log(cursor)
        return {
            "message": "editorState",
            "data": {
                "source": source,
                "cursor": cursor,
                "filename": "iterm.sh",
            }
        }

    async def set_coords(self, keypress=False):
        app = await iterm2.async_get_app(self.connection)
        if app.current_window is None:
            return
        session = app.current_window.current_tab.current_session
        screen_contents = await session.async_get_screen_contents()
        self.command_start_coords = screen_contents.cursor_coord
        if keypress:
            self.command_start_coords.x -= 1
        log("Setting command_start_coords", self.command_start_coords.y, self.command_start_coords.x)
        source, cursor = await self.get_prompt_and_cursor()
        log("editorState:")
        log(source)
        log(cursor)

    async def clear_state(self):
        log("RETURN pressed, setting command_running = True")
        self.command_running = True
        log("Set self.command_running", self.command_running)
        source, cursor = await self.get_prompt_and_cursor()
        log("previous editorState:", source, cursor)
        await self.set_coords()
        pass

    async def start_command(self):
        # If command is running, then we know we are just starting a new command,
        # so use the current cursor to mark where the command should start
        if self.command_running:
            log("Other key pressed, marking command start at cursor")
            self.command_running = False
            await self.set_coords(keypress=True)

    async def check_keystroke(self, keystroke):
        if keystroke.keycode == iterm2.keyboard.Keycode.RETURN or \
            (
                iterm2.keyboard.Modifier.CONTROL in keystroke.modifiers and
                (keystroke.keycode == iterm2.keyboard.Keycode.ANSI_C or
                 keystroke.keycode == iterm2.keyboard.Keycode.ANSI_D)
                    ):
            await self.clear_state()
        else:
            await self.start_command()
