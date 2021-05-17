#!/bin/bash
# Lint yaml

sudo pip install yamllint
yamllint -c ./scripts/linting/yaml-lint-config.yml --strict .
