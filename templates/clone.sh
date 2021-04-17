#!/bin/bash
# args are <git repo> <commit hash>

set -e

echo "Running clone $@"

CWD="$PWD"

[ -s picongpu/include/picongpu/CMakeLists.txt ] && exit 0
[ -d picongpu ] && rm -fr picongpu
mkdir -p picongpu

pushd "$1"
git archive "$2" | tar -x -C "$CWD/picongpu"
popd

if [ ! -s picongpu/include/picongpu/CMakeLists.txt ]; then
  echo "Cloning unsuccessful."
  rm -fr picongpu
  exit 1
fi
