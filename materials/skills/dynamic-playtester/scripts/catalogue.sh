#!/usr/bin/env bash
# catalogue.sh <genre> : construit references/bugs-arcade.md dans une session pi séparée.
# Cette session ne connaît pas le bug en cours, elle cherche donc sur tous les composants
# au lieu de s'arrêter au symptôme. Elle reprend le modèle de la session appelante.
set -euo pipefail
DIR=$(cd "$(dirname "$0")/.." && pwd)
GENRE=${1:?usage: catalogue.sh <genre>}
MODEL=${PI_MODEL:+${PI_PROVIDER:+$PI_PROVIDER/}$PI_MODEL}

# Chercher et résumer demande peu de raisonnement : --thinking low divise le temps de génération.
# La collecte passe par codemode : un script lance toutes les recherches de pi-web-access
# et ouvre les pages en un seul tour, au lieu d'un tour de modèle par appel.
pi -p --no-session --no-skills --no-context-files --thinking low \
  --tools codemode,web_search,fetch_content,read,write \
  ${MODEL:+--model "$MODEL"} \
  "$(cat "$DIR/references/consignes-catalogue.md")

Genre : $GENRE
Fichier : $DIR/references/bugs-arcade.md"

test -s "$DIR/references/bugs-arcade.md" && grep -c '^#### ' "$DIR/references/bugs-arcade.md" | sed 's/$/ entrées au catalogue/'
