#!/bin/bash
# Lint yaml

yamllint -c ./scripts/linting/yaml-lint-config.yml --strict .
