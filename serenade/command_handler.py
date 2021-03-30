import iterm2

from build_command import build_command
from count_cursor import count_cursor


class CommandHandler:
    def __init__(self, connection):
        self.connection = connection
        self.undo_index = 0
        self.command_stack = []
        self.last_command_was_use = False
        pass

    async def handle(self, response):
        result = None

        # print(response)
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

                # print(command)

        return result

    async def diff(self, data, command_type=""):
        # print("diff", data, command_type)

        source, cursor = await self.get_prompt_and_cursor()

        text = data.get("insertDiff", "")
        if text.endswith("\n"):
            text = text[:-1]

        delete = data.get("deleteEnd") is not None and \
            data.get("deleteStart") is not None and \
            data.get("deleteEnd") - data.get("deleteStart") != 0
        new_cursor = data.get("deleteEnd") if delete else data.get("cursor")
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
                # print("Deleting from", source, data.get("deleteStart"), data.get("deleteEnd"))
                data["deleted"] = source[data.get("deleteStart"):data.get("deleteEnd")]
            # If it's a use command, push this as the last valid command
            if command_type == "use":
                # Remember the original command's deleted text
                data["deleted"] = self.command_stack[self.undo_index - 1]["deleted"]
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

        # print("Adjusting cursor by", cursor_adjustment)
        # print("Deleting by", delete_count)
        # print("Inserting", text)

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
        prompt = await iterm2.async_get_last_prompt(self.connection, session.session_id)
        if prompt:
            command_coord = prompt.command_range.start
            screen_contents = await session.async_get_screen_contents()
            line_info = await session.async_get_line_info()
            cursor_coord = screen_contents.cursor_coord
            command = build_command(command_coord, screen_contents, line_info)
            cursor = count_cursor(command_coord, cursor_coord, session.grid_size.width)
            if cursor > len(command):
                return command, len(command)
            return command, cursor
        return "", 0

    async def get_editor_state(self):
        source, cursor = await self.get_prompt_and_cursor()
        # print(source, cursor)
        return {
            "message": "editorState",
            "data": {
                "source": source,
                "cursor": cursor,
                "filename": "iterm.sh",
            }
        }
