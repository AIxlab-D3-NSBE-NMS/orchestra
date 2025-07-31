.PHONY: setup

setup:
    uv venv .venv
    source .venv/bin/activate && uv pip install -e . && uv pip install -r requirements.txt

