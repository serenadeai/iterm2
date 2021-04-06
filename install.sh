#!/bin/bash

set -e

echo "Cloning git@github.com:serenadeai/iterm2.git to ~/.serenade/iterm2"
git clone --depth 1 https://github.com/serenadeai/iterm2.git ~/.serenade/iterm2

directory="$HOME/.serenade/iterm2"
destination="$HOME/Library/Application Support/iTerm2/Scripts"

echo "Adding symlinks to:"
echo "$destination"
echo
(set -x; mkdir -p "$destination")
(set -x; ln -s "$directory"/serenade "$destination")
(set -x; ln -s "$directory"/AutoLaunch.scpt "$destination")
echo "Done!"
