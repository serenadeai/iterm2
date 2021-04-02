# Serenade for iTerm2

## Installation

1. Download and install iTerm2 from https://iterm2.com if not installed already.
1. Run the below to install the Serenade plugin:
   ```
   curl https://raw.githubusercontent.com/serenadeai/iterm2/main/install.sh | bash
   ```
1. Restart iTerm2, and you should automatically be prompted to install a Python runtime for scripts:
    <img src="readme/runtime_prompt.png" width=200 />
    - If not, you can install by Python runtime manually via the menu item under Scripts > Manage > Install Python Runtime.
1. Enable iTerm2's [Python API](https://iterm2.com/python-api-auth.html). You can do this by either:
    - starting the Serenade script manually for the first time, via clicking Scripts > serenade > serenade.py
    - _or_ by enabling the Python API with iTerm2 > Preferences... > General > Magic > Enable Python API

Now, the AutoLaunch script should start the Serenade script every time iTerm2 is started.

### Updates

The client app will check and update the plugin each time it's started, but you can manually update with:

    git -C ~/.serenade/iterm2 pull

### Manual installation

If you prefer to not run an installation script directly, you can view it at https://raw.githubusercontent.com/serenadeai/iterm2/main/install.sh and run each line manually.

### Uninstallation

Run the following to uninstall the shell integration and Serenade scripts:

   curl https://raw.githubusercontent.com/serenadeai/iterm2/main/uninstall.sh | bash

## Development

1. After installation, use Scripts > Manage > console to restart the script and see output after making changes to files in `~/.serenade/iterm2`.

### Implementation details

#### Layout

In `serenade.py`, when the script is launched in iTerm, for every new session a new instance of the `CommandHandler` class is created, along with the `Ipc` class needed to communicate with the client. iTerm provides a single global [Connection](https://iterm2.com/python-api/connection.html) API through which all requests with the terminal is made.

##### CommandHandler

`CommandHandler` supports these commands:

- `COMMAND_TYPE_GET_EDITOR_STATE`, which uses the [Prompt](https://iterm2.com/python-api/prompt.html), [Session](https://iterm2.com/python-api/session.html) and [Screen](https://iterm2.com/python-api/screen.html) API to get the source (drafted command at the prompt) and cursor
