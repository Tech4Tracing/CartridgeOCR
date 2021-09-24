#!/bin/bash
# Lint markdown

sudo npm install -g markdownlint-cli
markdownlint . -c ./scripts/linting/markdownlint.config
