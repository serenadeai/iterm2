def build_command(command_coord, screen_contents, line_info):
    command = ""
    # command_coord.y is an absolute line number, while screen.contents.line expects a relative line number
    # For example, if there are a total of 20 lines, 10 of which are off-screen, command_coord.y will be 20,
    # and the last visible line will be indexed to 10 instead of 20.
    current_line = command_coord.y - line_info.first_visible_line_number
    # So we go from the first line of the command to the end of the screen, and build the command
    # with the contents of each line.
    while line_info.first_visible_line_number <= current_line < screen_contents.number_of_lines:
        line = screen_contents.line(current_line).string
        # The first line should be offset by the x-coordinate of the command.
        if current_line == command_coord.y - line_info.first_visible_line_number:
            command += line[command_coord.x:]
        # The last line should have whitespace trimmed with no newlines
        elif current_line == screen_contents.number_of_lines - 1:
            command += line.rstrip()
        # Other lines should be trimmed as well.
        else:
            command += line + "\n" if line.rstrip() else ""
        current_line += 1
    return command.rstrip()
