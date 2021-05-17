#!/bin/bash
# Lint yaml

pip install yamllint
yamllint -c ./scripts/linting/yaml-lint-config.yml --strict .
