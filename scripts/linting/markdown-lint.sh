#!/bin/bash
# Lint markdown

npm install -g markdownlint-cli
markdownlint . -c ./scripts/linting/markdown-lint.config
