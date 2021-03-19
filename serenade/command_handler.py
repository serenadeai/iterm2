import iterm2


class CommandHandler:
    def __init__(self, connection):
        self.connection = connection
        pass

    async def handle(self, response):
        result = {}

        # print(response)
        if response.get("execute"):
            for command in response.get("execute").get("commandsList"):
                command_type = command.get("type")

                if command_type == "COMMAND_TYPE_DIFF":
                    result = await self.diff(command)
                if command_type == "COMMAND_TYPE_GET_EDITOR_STATE":
                    result = await self.get_editor_state()

                # print(command)

        return result

    async def diff(self, data):
        source, cursor = await self.get_prompt_and_cursor()

        text = data.get("insertDiff")
        if text.endswith("\n"):
            text = text[:-1]

        delete = data.get("deleteEnd") is not None and \
            data.get("deleteStart") is not None and \
            data.get("deleteEnd") - data.get("deleteStart") != 0
        new_cursor = data.get("deleteEnd") if delete else data.get("cursor")
        delete_count = data.get("deleteEnd", 0) - data.get("deleteStart", 0)

        # print(f"Adjusting cursor by {new_cursor - cursor}")
        # print(f"Deleting by {delete_count}")
        # print(f"Inserting {text}")

        return {
            "message": "applyDiff",
            "data": {
                "adjustCursor": new_cursor - cursor,
                "deleteCount": delete_count,
                "text": text
            }
        }

    async def get_prompt_and_cursor(self):
        app = await iterm2.async_get_app(self.connection)
        session = app.current_window.current_tab.current_session
        prompt = await iterm2.async_get_last_prompt(self.connection, session.session_id)
        if prompt:
            command_range = prompt.command_range
            screen_contents = await session.async_get_screen_contents()
            cursor = screen_contents.cursor_coord.x - command_range.start.x
            return prompt.command, cursor
        return "", 0

    async def get_editor_state(self):
        source, cursor = await self.get_prompt_and_cursor()
        return {
            "message": "editorState",
            "data": {
                "source": source,
                "cursor": cursor,
                "filename": "iterm.sh",
            }
        }
