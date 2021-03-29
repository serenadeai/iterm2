#!/bin/bash

set -e

echo "Cloning git@github.com:serenadeai/iterm2.git to ~/.serenade/iterm2"
git clone git@github.com:serenadeai/iterm2.git ~/.serenade/iterm2

if [[ $SHELL == *"bash"* ]]; then
  echo "Adding ~/.serenade/iterm2/bin/serenade-shell-integration.bash to ~/.bash_profile"
  echo "source ~/.serenade/iterm2/bin/serenade-shell-integration.bash" >> ~/.bash_profile
elif [[ $SHELL == *"zsh"* ]]; then
  echo "Adding ~/.serenade/iterm2/bin/serenade-shell-integration.zsh to ~/.zshrc"
  echo "source ~/.serenade/iterm2/bin/serenade-shell-integration.zsh" >> ~/.zshrc
fi

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
dest="$HOME/Library/Application Support/iTerm2/Scripts"

echo "Adding symlinks to:"
echo "$dest"
echo
(set -x; mkdir -p "$dest")
(set -x; ln -s "$dir"/serenade "$dest")
(set -x; ln -s "$dir"/AutoLaunch.scpt "$dest")
echo "Done!"
