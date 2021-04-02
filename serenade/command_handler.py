import iterm2


DEBUG = False


def log(*args):
    if DEBUG:
        print("CoH:", *args)


class CommandHandler:
    def __init__(self, connection, session_id, session):
        self.connection = connection
        self.session_id = session_id
        self.session = session

        # Editor state
        self.command_start_coords = None
        self.clear_screen_pressed = False
        self.last_line = None
        self.update_on_render = True

    async def keyboard_listener(self):
        async with iterm2.KeystrokeMonitor(self.connection, self.session_id) as mon:
            while True:
                keystroke = await mon.async_get()
                await self.check_keystroke(keystroke)

    async def screen_listener(self):
        async with self.session.get_screen_streamer() as streamer:
            while True:
                screen_contents = await streamer.async_get()
                line_info = await self.session.async_get_line_info()
                line_changed = False

                # We're on a different line than before
                if self.command_start_coords and self.command_start_coords.y != screen_contents.cursor_coord.y:
                    line_changed = True
                    # Unless the new line is from a wrapped line, so try to look up 2 lines and see if it's the same
                    current_line = (
                        screen_contents.cursor_coord.y - line_info.first_visible_line_number
                    )
                    if current_line > 2 and screen_contents.line(current_line - 2).string == self.last_line:
                        line_changed = False
                    # Otherwise update the last line if we can
                    elif screen_contents.number_of_lines > current_line > 1:
                        self.last_line = screen_contents.line(current_line - 1).string

                log("Screen output changed, update_on_render is", self.update_on_render)
                if self.update_on_render:
                    await self.update_prompt(screen_contents=screen_contents)
                elif line_changed:
                    log("Updating prompt since line_changed")
                    await self.update_prompt(screen_contents=screen_contents)
                elif DEBUG:
                    source, cursor = await self.get_prompt_and_cursor(screen_contents=screen_contents)
                    log(f"editorState: '{source}', {cursor}")

    async def check_keystroke(self, keystroke):
        # For enter and keys with modifiers, clear the state so we can update the cursor
        if keystroke.keycode == iterm2.keyboard.Keycode.RETURN or len(
            keystroke.modifiers
        ):
            # Clearing the screen with control+L doesn't remove the command
            if (
                iterm2.keyboard.Modifier.CONTROL in keystroke.modifiers
                and keystroke.keycode == iterm2.keyboard.Keycode.ANSI_L
            ):
                self.clear_screen_pressed = True
            self.update_on_render = True
            self.last_line = None
        else:
            self.update_on_render = False

    async def handle(self, response):
        result = None

        if response.get("execute"):
            for command in response.get("execute").get("commandsList"):
                command_type = command.get("type")
                if command_type == "COMMAND_TYPE_GET_EDITOR_STATE":
                    result = await self.get_editor_state(limited=command.get("limited"))
        return result

    async def get_editor_state(self, limited):
        if limited:
            return {
                "message": "editorState",
                "data": {
                    "filename": "iterm.sh",
                },
            }

        source, cursor = await self.get_prompt_and_cursor()
        log(f"editorState: '{source}', {cursor}")
        return {
            "message": "editorState",
            "data": {
                "source": source,
                "cursor": cursor,
                "filename": "iterm.sh",
            },
        }

    async def get_prompt_and_cursor(self, screen_contents=None):
        if screen_contents is None:
            screen_contents = await self.session.async_get_screen_contents()
        source, line_count = await self.get_source(screen_contents=screen_contents)
        # If the cursor is on the first character of the next line, that counts as a line
        line_count = max(
            screen_contents.cursor_coord.y - self.command_start_coords.y + 1, line_count
        )
        cursor = (
            screen_contents.cursor_coord.x
            - self.command_start_coords.x
            + self.session.grid_size.width * (line_count - 1)
        )
        if len(source) < cursor:
            source += " " * (cursor - len(source))
        return source, cursor

    async def update_prompt(self, screen_contents=None):
        if screen_contents is None:
            screen_contents = await self.session.async_get_screen_contents()
        # When the screen is cleared, then we only want to update the row, since
        # there might be text in the prompt already
        if self.clear_screen_pressed:
            self.command_start_coords.y = screen_contents.cursor_coord.y
            self.clear_screen_pressed = False
        else:
            self.command_start_coords = screen_contents.cursor_coord

    async def get_source(self, screen_contents=None):
        if screen_contents is None:
            screen_contents = await self.session.async_get_screen_contents()
        line_info = await self.session.async_get_line_info()
        command_start_line = (
            self.command_start_coords.y - line_info.first_visible_line_number
        )

        command = ""
        i = command_start_line
        while i < screen_contents.number_of_lines:
            line = screen_contents.line(i).string
            # We stop after the first empty line
            if len(line.rstrip()) == 0:
                break
            # The first line should be offset by the x-coordinate of the command.
            if i == command_start_line:
                command += line[self.command_start_coords.x :]
            # The last line should have whitespace trimmed with no newlines
            elif i == screen_contents.number_of_lines - 1:
                command += line.rstrip()
            else:
                command += line
            i += 1
        return command.rstrip(), i - command_start_line
