#!/usr/bin/env bash

# Exit early if something goes wrong
set -x

# Add commands below to run as part of the post_build phase

ls -al /layers/paketo-buildpacks_pipenv-install/packages/

which python

python --version

pipenv install --deploy --verbose