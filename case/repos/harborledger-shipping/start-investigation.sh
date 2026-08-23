#!/bin/sh
# Restore the seized server image of the shipping firm:
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$DIR/.git"
cp -R "$DIR/.gitarchiv" "$DIR/.git"
echo "Image restored. From now on: cd into this directory and use git."
