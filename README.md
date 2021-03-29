# Serenade for iTerm2

## Installation

1. Download iTerm from https://iterm2.com/index.html if not installed already.
1. Run the following to automatically install the shell integration and Serenade scripts:
   ```
   curl https://raw.githubusercontent.com/serenadeai/iterm2/main/install.sh | bash
   ```
1. Restart iTerm, and you should automatically be prompted to install a Python runtime for scripts:
   <img src="readme/runtime_prompt.png" width=200 />
    - Alternatively, you can use the menu item under Scripts > Manage > Install Python Runtime.
    
### Manual installation

If you prefer to not run an installation script directly, you can view it at https://raw.githubusercontent.com/serenadeai/iterm2/main/install.sh and run each line manually.

## Development

1. After installation, use Scripts > Manage > console to restart the script and see output after making changes to files here.

## Supported commands

- Add/change/delete
- Go to
- Undo/redo

### Implementation details

#### Shell integration

In the `bin` directory of [serenade-hyper](https://github.com/serenadeai/serenade-hyper/tree/main/bin), shell scripts based on [iTerm2's shell integration](https://iterm2.com/documentation-shell-integration.html) tells the shell to send additional escape codes that indicate the start and end of the prompt and output. This is automatically handled by iTerm to determine the prompt's contents and position on screen.

#### Layout

In `serenade.py`, when the script is launched in iTerm, a new instance of the `CommandHandler` class is created, along with the `Ipc` class needed to communicate with the client. iTerm provides a single global [Connection](https://iterm2.com/python-api/connection.html) API through which all requests with the terminal is made.

##### CommandHandler

`CommandHandler` supports four commands:
- `COMMAND_TYPE_GET_EDITOR_STATE`, which uses the [Prompt](https://iterm2.com/python-api/prompt.html), [Session](https://iterm2.com/python-api/session.html) and [Screen](https://iterm2.com/python-api/screen.html) API to get the source (drafted command at the prompt) and cursor
- `COMMAND_TYPE_DIFF`, which determines the adjustments to the source and cursor needed, and responds to the client to perform some subset of moving the cursor, deleting a number of characters, and inserting additional characters
- `COMMAND_TYPE_UNDO`, which uses an internal stack of commands to send an inverse of a previous command to the client via `COMMAND_TYPE_DIFF`
- `COMMAND_TYPE_REDO`, which sends previous commands to the client via `COMMAND_TYPE_DIFF`
