# src/nova_forge/core/tmpl_workflow.py

WORKFLOW_TMPL = """name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:  # ✅ 支持手动触发发版

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Build package
      run: |
        python -m pip install --upgrade pip
        pip install build
        python -m build

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
"""
