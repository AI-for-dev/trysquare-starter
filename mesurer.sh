#!/usr/bin/env bash
#
# trysquare, lancé depuis le venv de ce dépôt, avec la config de ce dépôt, et
# une ligne de journal par mesure.
#
#   ./mesurer.sh                              la matrice du scénario par défaut
#   ./mesurer.sh --dry-run                    le plan, sans rien dépenser
#   ./mesurer.sh --repetitions 3              une passe de fumée
#   ./mesurer.sh issue1-contexte --dry-run    en nommant le scénario
#   ./mesurer.sh render results/issue1-…      une sous-commande, telle quelle
#
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SORTIE="${SORTIE:-$ICI/results}"
DEFAUT=issue1-contexte

if [ ! -x "$ICI/.venv/bin/trysquare" ]; then
  echo "Le venv est absent : lancez ./setup.sh d'abord." >&2
  exit 1
fi

# Le venv en tête du PATH plutôt qu'un appel au chemin complet. trysquare lance
# le validateur en sous-processus, et `validateurs/issue1.py` importe
# `trysquare.assay` sous un shebang `/usr/bin/env python3` : sans cette ligne il
# tomberait sur le python du système, qui ne connaît pas le paquet.
export PATH="$ICI/.venv/bin:$PATH"

# `trysquare.toml` place les clones jetables sous `$TMPDIR`, que Linux ne définit
# pas toujours alors que macOS le fait. Sans repli, le chemin commencerait par
# une chaîne vide et les clones atterriraient à la racine du dépôt.
export TMPDIR="${TMPDIR:-/tmp}"

case "${1:-}" in
  render|replay|compare|--help|-h)
    exec trysquare "$@"
    ;;
esac

SCENARIO="$DEFAUT"
if [ "${1:-}" != "" ] && [ -f "$ICI/scenarios/$1.toml" ]; then
  SCENARIO="$1"; shift
fi
CHEMIN="$ICI/scenarios/$SCENARIO.toml"
[ -f "$CHEMIN" ] || { echo "scénario inconnu : $SCENARIO" >&2; exit 2; }

cd "$ICI"
trysquare run "scenarios/$SCENARIO.toml" --output "$SORTIE" "$@"

# Le journal n'est écrit que pour une mesure qui a réellement dépensé. Il garde
# la révision de ce dépôt et la version de trysquare, que le scénario ne dit pas :
# lui n'épingle que le dépôt mesuré, par son tag.
for arg in "$@"; do
  [ "$arg" = "--dry-run" ] && exit 0
done

revision="$(git -C "$ICI" rev-parse --short HEAD 2>/dev/null || echo 'hors dépôt')"
git -C "$ICI" diff --quiet 2>/dev/null || revision="$revision-dirty"
mkdir -p "$SORTIE"
printf '| %s | %s | %s | trysquare %s | harnais %s |\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  "$SCENARIO" \
  "${*:-(aucune option)}" \
  "$(trysquare --version 2>/dev/null || echo '?')" \
  "$revision" \
  >> "$SORTIE/journal.md"
