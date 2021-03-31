from iterm2 import Point


# Using the width of the screen and x, y coordinates of the command
# start and the cursor, calculate the number of characters from the
# start to the cursor.
def count_cursor(command_coord_start, cursor_coord, screen_width):
    cursor = 0
    current_line = command_coord_start.y
    while current_line < cursor_coord.y:
        if current_line == command_coord_start.y:
            cursor += screen_width - command_coord_start.x
        else:
            cursor += screen_width
        current_line += 1
    if current_line == command_coord_start.y:
        cursor += cursor_coord.x - command_coord_start.x
    else:
        cursor += cursor_coord.x
    return cursor


assert (count_cursor(Point(0, 0), Point(0, 0), 10) == 0)
assert (count_cursor(Point(0, 0), Point(1, 0), 10) == 1)
assert (count_cursor(Point(0, 0), Point(0, 1), 10) == 10)
assert (count_cursor(Point(0, 0), Point(1, 1), 10) == 11)
assert (count_cursor(Point(0, 0), Point(1, 2), 10) == 21)
assert (count_cursor(Point(0, 2), Point(1, 2), 10) == 1)
