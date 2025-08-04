FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
LABEL authors="giumartine"

WORKDIR /home
COPY .. .

RUN uv init
RUN uv add -r ./requirements.txt

ENTRYPOINT [".venv/bin/python3", "./main.py", "$@"]