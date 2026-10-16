#!/usr/bin/env bash
# catalogue.sh <genre>: builds references/bugs-arcade.md in a separate pi session.
# That session knows nothing of the current bug, so it searches every component
# instead of stopping at the symptom. It uses the model of the calling session.
set -euo pipefail
DIR=$(cd "$(dirname "$0")/.." && pwd)
GENRE=${1:?usage: catalogue.sh <genre>}
MODEL=${PI_MODEL:+${PI_PROVIDER:+$PI_PROVIDER/}$PI_MODEL}
CATALOGUE="$DIR/references/bugs-arcade.md"
# The session is kept beside the skill, and not thrown away: check-sources.mjs reads the pages
# the search returned from it.
SESSION="$DIR/references/catalogue-session"
mkdir -p "$SESSION"

# Searching and summarising needs little reasoning: --thinking low cuts the generation time.
# The collection goes through codemode: one script runs every pi-web-access search
# and opens the pages in a single turn, instead of one model turn per call.
status=0
pi -p --session-dir "$SESSION" --no-skills --no-context-files --thinking low \
  --tools codemode,web_search,fetch_content,read,write \
  ${MODEL:+--model "$MODEL"} \
  "$(cat "$DIR/references/catalogue-instructions.md")

Genre: $GENRE
File: $CATALOGUE" || status=$?

# Only the entries whose source is a page the search opened stay in the catalogue.
# It runs even when pi failed, since pi may have written the file before it did.
node "$DIR/scripts/check-sources.mjs" "$SESSION" "$CATALOGUE"
exit "$status"
