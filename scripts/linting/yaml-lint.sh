#!/bin/bash
# Lint yaml

sudo pip install yamllint
yamllint -c ./scripts/linting/yamllintconfig.yml --strict .
