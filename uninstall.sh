#!/bin/bash

set -e

if [[ $SHELL == *"bash"* ]]; then
  echo "Removing ~/.serenade/iterm2/bin/serenade-shell-integration.bash from ~/.bash_profile"
  sed -i '' 's/source ~\/.serenade\/iterm2\/bin\/serenade-shell-integration.bash//g' ~/.bash_profile
elif [[ $SHELL == *"zsh"* ]]; then
  echo "Removing ~/.serenade/iterm2/bin/serenade-shell-integration.zsh from ~/.zshrc"
  sed -i -e 's/source ~\/.serenade\/iterm2\/bin\/serenade-shell-integration.zsh//g' ~/.zshrc
fi

dest="$HOME/Library/Application Support/iTerm2/Scripts"

echo "Removing symlinks from:"
echo "$dest"
rm -rf "$dest"/serenade
rm -f "$dest"/AutoLaunch.scpt

echo "Removing ~/.serenade/iterm2"
rm -rf ~/.serenade/iterm2

echo "Done!"
