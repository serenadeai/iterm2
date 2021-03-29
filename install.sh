#!/bin/bash

set -e

dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
dest="$HOME/Library/Application Support/iTerm2/Scripts"

echo "This script will symlink files from this directory to"
echo "$dest"
echo
read -p "Confirm (Y/N)? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    (set -x; mkdir -p "$dest")
    (set -x; ln -s "$dir"/serenade "$dest")
    (set -x; ln -s "$dir"/AutoLaunch.scpt "$dest")
    echo "Done!"
fi
