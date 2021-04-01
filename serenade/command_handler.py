import asyncio
import iterm2
import re


DEBUG = False


def log(*args):
    if DEBUG:
        print(*args)


class CommandHandler:
    def __init__(self, connection, session_id):
        self.connection = connection
        self.session_id = session_id

        # Editor state
        self.command_start_coords = None
        self.empty_line_regex = re.compile(r"^\s*$")
        self.update_on_render = True
        self.prompt = {
            "offset_left": 0,
            "buffer_index": 0
        }

        # Undo stack
        self.undo_index = 0
        self.command_stack = []
        self.last_command_was_use = False

    async def keyboard_listener(self):
        app = await iterm2.async_get_app(self.connection)
        async with iterm2.KeystrokeMonitor(self.connection) as mon:
            while True:
                keystroke = await mon.async_get()
                session = app.get_session_by_id(self.session_id)
                if session and session.window is app.current_window:
                    await self.check_keystroke(keystroke)

    async def screen_listener(self):
        app = await iterm2.async_get_app(self.connection)
        while True:
            if app.current_window:
                session = app.current_window.current_tab.current_session
                log(session)
                async with session.get_screen_streamer() as streamer:
                    while True:
                        await streamer.async_get()
                        log("Screen output changed, update_on_render is", self.update_on_render)
                        if self.update_on_render:
                            await self.update_prompt()
                        else:
                            source, cursor = await self.get_prompt_and_cursor()
                            log(f"editorState: '{source}', {cursor}")
            await asyncio.sleep(1)
            log("retrying")

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
        session = app.current_window.current_tab.current_session
        i, screen_contents = await self.get_active_line_number()
        source = (await self.get_active_line())[self.prompt.get("offset_left"):]
        cursor = session.grid_size.width * (i - self.prompt.get("buffer_index")) + \
            screen_contents.cursor_coord.x - self.prompt.get("offset_left")
        if len(source) < cursor:
            source += " " * (cursor - len(source))
        return source, cursor

    async def get_editor_state(self):
        source, cursor = await self.get_prompt_and_cursor()
        log(f"editorState: '{source}', {cursor}")
        return {
            "message": "editorState",
            "data": {
                "source": source,
                "cursor": cursor,
                "filename": "iterm.sh",
            }
        }

    async def update_prompt(self):
        buffer_index, screen_contents = await self.get_active_line_number()
        log("Prompt updated to", buffer_index, screen_contents.cursor_coord.x)
        self.prompt = {
            "offset_left": screen_contents.cursor_coord.x,
            "buffer_index": buffer_index
        }

    async def get_active_line(self):
        i, screen_contents = await self.get_active_line_number()
        line = screen_contents.line(i).string.rstrip()
        while i > 0 and i != self.prompt.get("buffer_index"):
            line = screen_contents.line(i - 1).string + line
            i -= 1
        return line

    async def get_active_line_number(self):
        app = await iterm2.async_get_app(self.connection)
        session = app.current_window.current_tab.current_session
        screen_contents = await session.async_get_screen_contents()
        for i in range(screen_contents.number_of_lines - 1, -1, -1):
            if not screen_contents.line(i).hard_eol or \
                    self.empty_line_regex.search(screen_contents.line(i).string) is None:
                return i, screen_contents
        return 0, screen_contents

    async def check_keystroke(self, keystroke):
        # For enter, control+C, and control+D, clear the state so we can update the cursor
        if keystroke.keycode == iterm2.keyboard.Keycode.RETURN or \
            (
                iterm2.keyboard.Modifier.CONTROL in keystroke.modifiers and
                (keystroke.keycode == iterm2.keyboard.Keycode.ANSI_C or
                 keystroke.keycode == iterm2.keyboard.Keycode.ANSI_D)
                    ):
            self.update_on_render = True
        else:
            self.update_on_render = False

