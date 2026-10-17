#!/usr/bin/env bash
# catalogue.sh <genre>: builds references/bugs-arcade.md in a separate pi session.
# That session knows nothing of the current bug, so it searches every component
# instead of stopping at the symptom. It uses the model of the calling session.
set -euo pipefail
DIR=$(cd "$(dirname "$0")/.." && pwd)
GENRE=${1:?usage: catalogue.sh <genre>}
MODEL=${PI_MODEL:+${PI_PROVIDER:+$PI_PROVIDER/}$PI_MODEL}

# The session runs at --thinking medium.
# The collection goes through codemode: one script runs every pi-web-access search
# and opens the pages in a single turn, instead of one model turn per call.
pi -p --no-session --no-skills --no-context-files --thinking medium \
  --tools codemode,web_search,fetch_content,read,write \
  ${MODEL:+--model "$MODEL"} \
  "$(cat "$DIR/references/catalogue-instructions.md")

Genre: $GENRE
File: $DIR/references/bugs-arcade.md"

test -s "$DIR/references/bugs-arcade.md" && grep -c '^#### ' "$DIR/references/bugs-arcade.md" | sed 's/$/ entries in the catalogue/'
