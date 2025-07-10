#!/usr/bin/env bash
set -ex


curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"


uv pip install -r requirements.txt

make install && psql -a -d $DATABASE_URL -f database.sql