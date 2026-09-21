#!/usr/bin/env bash
#
# Prépare l'environnement jetable : le venv qui porte trysquare, et les outils
# que la mesure appelle en sous-processus (git, node, pi).
#
#   ./setup.sh              installe ce qui manque, en demandant avant pi
#   ./setup.sh --yes        n'interroge pas
#   ./setup.sh --no-pi      ne touche pas à pi, se contente de le vérifier
#   ./setup.sh --check      ne modifie rien, dit seulement ce qui manque
#
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Le fournisseur et le modèle que `scenarios/issue1-contexte.toml` déclare. Lus
# ici pour que le rappel de fin nomme ce qu'il faut réellement avoir configuré,
# plutôt qu'une valeur recopiée qui se périmerait dès le premier scénario copié.
PROVIDER="$(sed -n 's/^provider = "\(.*\)"$/\1/p' "$ICI/scenarios/issue1-contexte.toml" | head -1)"
MODEL="$(sed -n 's/^model = "\(.*\)"$/\1/p' "$ICI/scenarios/issue1-contexte.toml" | head -1)"

INSTALLEUR_PI="https://pi.dev/install.sh"
NODE_MIN=20

AUTO=0
SANS_PI=0
CHECK=0
for arg in "$@"; do
  case "$arg" in
    --yes|-y) AUTO=1 ;;
    --no-pi) SANS_PI=1 ;;
    --check) CHECK=1 ;;
    *) echo "argument inconnu : $arg" >&2; exit 2 ;;
  esac
done

manquant=0
note() { printf '  %s\n' "$*"; }
ligne() { printf '  %-9s %s\n' "$1" "$2"; }
absent() { printf '  manquant : %s\n' "$*"; manquant=1; }

echo "Prérequis"

for outil in git uv; do
  if command -v "$outil" >/dev/null 2>&1; then
    ligne "$outil" "$(command -v "$outil")"
  else
    absent "$outil"
  fi
done

# La sonde de notation tourne avec `node --test --test-reporter=…` sur un glob,
# et le validateur lit son JSON. Une version trop ancienne ne rendrait rien à lire.
if command -v node >/dev/null 2>&1; then
  node_version="$(node --version)"
  node_major="${node_version#v}"; node_major="${node_major%%.*}"
  if [ "$node_major" -ge "$NODE_MIN" ]; then
    ligne node "$node_version"
  else
    absent "node >= $NODE_MIN (trouvé $node_version)"
  fi
else
  absent "node >= $NODE_MIN"
fi

if command -v pi >/dev/null 2>&1; then
  ligne pi "$(pi --version 2>/dev/null || echo 'version illisible')"
elif [ "$CHECK" = 1 ] || [ "$SANS_PI" = 1 ]; then
  absent "pi (voir https://pi.dev)"
else
  echo
  echo "pi n'est pas sur le PATH. L'installateur officiel est :"
  echo
  echo "    curl -fsSL $INSTALLEUR_PI | sh"
  echo
  if [ "$AUTO" = 1 ]; then
    reponse=o
  else
    read -r -p "Le lancer maintenant ? [o/N] " reponse || reponse=n
  fi
  case "$reponse" in
    o|O|y|Y)
      curl -fsSL "$INSTALLEUR_PI" | sh
      command -v pi >/dev/null 2>&1 || {
        echo "pi reste introuvable après installation : ouvrez un nouveau shell," >&2
        echo "ou ajoutez son répertoire au PATH, puis relancez ./setup.sh --check." >&2
        manquant=1
      }
      ;;
    *) absent "pi (voir https://pi.dev)" ;;
  esac
fi

if [ "$manquant" = 1 ] && [ "$CHECK" != 1 ]; then
  echo
  echo "Installez ce qui manque, puis relancez ./setup.sh." >&2
  exit 1
fi

if [ "$CHECK" = 1 ]; then
  echo
  [ "$manquant" = 0 ] && echo "Rien ne manque." || echo "Il manque des prérequis."
  exit "$manquant"
fi

echo
echo "Environnement Python"
# trysquare vient de TestPyPI et ses dépendances de PyPI ; `pyproject.toml` porte
# cette règle, et `uv.lock` garde la résolution exacte d'une machine à l'autre.
( cd "$ICI" && uv sync )
ligne trysquare "$("$ICI/.venv/bin/trysquare" --version 2>/dev/null || echo 'version illisible')"

echo
echo "Fournisseur de modèles"
# La clé d'API ne peut pas venir d'ici : elle est personnelle, et `models.json`
# est le fichier que pi lit. Le dire maintenant évite de le découvrir à la
# première cellule lancée, c'est-à-dire après avoir attendu un clone.
MODELS="$HOME/.pi/agent/models.json"
if [ -f "$MODELS" ]; then
  note "$MODELS existe"
  if grep -q "\"$PROVIDER\"" "$MODELS" 2>/dev/null; then
    note "il déclare le fournisseur « $PROVIDER » attendu par le scénario"
  else
    note "il ne déclare pas « $PROVIDER » : ajoutez-le, ou changez [agent] dans"
    note "scenarios/issue1-contexte.toml pour un fournisseur que vous avez."
  fi
else
  note "$MODELS est absent."
  note "Le scénario demande le fournisseur « $PROVIDER » et le modèle « $MODEL » ;"
  note "la forme du fichier est décrite sur https://pi.dev/docs/latest/providers."
fi

cat <<FIN

Prêt. La suite, dans l'ordre :

    ./mesurer.sh --dry-run          le plan complet, sans rien dépenser
    ./mesurer.sh --repetitions 3    une passe de fumée
    ./mesurer.sh                    la matrice du scénario, 20 répétitions
FIN
