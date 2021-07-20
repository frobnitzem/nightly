#!/bin/bash
# args are <git repo> <commit hash>

set -e

echo "Running clone $@"

CWD="$PWD"

[ -d BerkeleyGW ] && rm -fr BerkeleyGW
mkdir -p BerkeleyGW

pushd "$1"
git archive "$2" | tar -x -C "$CWD/BerkeleyGW"
popd

if [ ! -s BerkeleyGW/Makefile ]; then
  echo "Cloning unsuccessful."
  rm -fr BerkeleyGW
  exit 1
fi
