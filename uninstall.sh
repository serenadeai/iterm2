#!/bin/bash

set -e

destination="$HOME/Library/Application Support/iTerm2/Scripts"

echo "Removing symlinks from:"
echo "$destination"
rm -rf "$destination"/serenade
rm -f "$destination"/AutoLaunch.scpt

echo "Removing ~/.serenade/iterm2"
rm -rf ~/.serenade/iterm2

echo "Done!"
