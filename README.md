# trysquare-starter

De quoi rejouer une seule expérience de la formation, `issue1-contexte`, dans un
environnement qu'on jette après : les leviers de contexte du module 2.1 mesurés
contre le rebond de l'issue #1 de NÉON, neuf configurations, un levier à la fois.

Le dépôt ne contient pas l'outil de mesure. [trysquare](https://github.com/AI-for-dev/trysquare)
est un paquet Python installé dans un venv local ; ce qui vit ici est le
matériau de l'expérience, c'est-à-dire le scénario, les briques, l'hypothèse
écrite avant la mesure, et le validateur qui note.

## Démarrer

```bash
./setup.sh                      # prérequis, venv, trysquare, rappel sur le fournisseur
./mesurer.sh --dry-run          # le plan complet, sans rien dépenser
./mesurer.sh --repetitions 3    # une passe de fumée
./mesurer.sh                    # la matrice, 20 répétitions par configuration
```

`setup.sh` vérifie `git`, `node` et `uv`, propose d'installer `pi` avec
l'installateur de [pi.dev](https://pi.dev) s'il manque, puis lance `uv sync`.
Ce dernier crée `.venv` et écrit `uv.lock`, qui épingle trysquare et ses
dépendances. Le scénario épingle déjà le dépôt mesuré par un tag ; ce verrou
épingle l'outil qui le mesure, sans quoi deux machines rendraient deux matrices
sans qu'on sache laquelle a changé. `./setup.sh --check` ne modifie rien et dit
seulement ce qui manque.

`mesurer.sh` met `.venv/bin` en tête du `PATH`, donne à `$TMPDIR` un repli
`/tmp`, écrit dans `results/`, et ajoute une ligne à `results/journal.md` pour
toute mesure qui a réellement dépensé. Un `-dirty` dans cette ligne signale une
mesure qu'on ne saura pas reproduire exactement. Les sous-commandes qui ne
dépensent rien passent telles quelles :

```bash
./mesurer.sh render results/issue1-contexte_…
./mesurer.sh replay results/issue1-contexte_… --scenario scenarios/issue1-contexte.toml --rescore
./mesurer.sh compare results/… results/…
```

## Ce qu'il faut avoir avant

| prérequis | pourquoi |
| --- | --- |
| `uv` | crée le venv et installe trysquare |
| `node` >= 20 | la sonde de notation est une suite `node:test`, lancée avec `--test-reporter` |
| `git` | trysquare clone NÉON sur son tag, et le validateur y lit sa référence |
| `pi` | le harnais mesuré, installé depuis [pi.dev](https://pi.dev) |
| un fournisseur de modèles | déclaré dans `~/.pi/agent/models.json`, voir [la documentation de pi](https://pi.dev/docs/latest/providers) |
| un accès réseau | GitHub pour NÉON et l'extension, TestPyPI et PyPI pour l'installation, le fournisseur pour les appels |

Le scénario déclare son fournisseur et son modèle dans sa table `[agent]`,
parce que ce sont les deux valeurs qui décident de ce qui est mesuré et qu'un
héritage depuis le shell les rendrait invisibles au lecteur du fichier. Si vous
n'avez pas ce fournisseur, changez ces deux lignes avant de lancer. Les tables
publiées dans le cours ont été mesurées sur `ilaas` et `gemma-4-31b`, contre le
commit `d62ccd1f` de NÉON.

## Le coût

Vingt répétitions sur neuf configurations demandent deux à trois heures et les
jetons qui vont avec. Commencez par `--dry-run`, qui ne dépense rien, puis par
`--repetitions 3`, qui suffit à voir la dispersion : le nom du répertoire de
sortie porte le nombre de répétitions, donc une passe de fumée ne se confond pas
avec la vraie matrice.

## Disposition

```
trysquare-starter/
  pyproject.toml     d'où vient trysquare, et rien d'autre
  setup.sh           prérequis, venv, rappel sur le fournisseur
  mesurer.sh         l'outil, la config, et la trace de ce qui a tourné
  trysquare.toml     chemins machine : où est NÉON, où vivent les clones jetables
  scenarios/         l'expérience, en un fichier TOML autonome
  hypotheses/        ce qui est prédit, écrit avant de mesurer
  briques/           prompts, AGENTS.md, prompt système, compétence, sonde
  validateurs/       ce qui note
  results/           une matrice par répertoire, plus le journal
```

Les chemins d'un scénario sont relatifs au scénario, ce qui rend le répertoire
déplaçable d'un bloc.

## L'expérience

Neuf configurations, dont une base `nothing` qui ne déclare aucun delta et
reproduit ce que fait quelqu'un le premier jour : la demande négligée, pas de
fichier de règles, pas de budget de raisonnement, le prompt système de l'agent.
Chacune des autres ajoute ou retire une pièce, et le fichier
`scenarios/issue1-contexte.toml` dit en commentaire pourquoi chacune est là.

Le critère est `rebond_briques`, et c'est une sonde plutôt qu'un motif dans le
diff : `briques/sonde-fournie/sonde.test.js` pose une balle déjà en recouvrement
avec une brique, appelle `frame()`, et regarde quelle composante de vitesse
s'inverse. Ce que l'issue #1 demande est un comportement, que la sonde exécute,
là où un motif cherché dans le diff dépendrait de la façon dont l'agent a écrit
sa correction.

Le validateur rend onze métriques, que le scénario déclare une à une. Une
métrique déclarée mais absente du validateur ne coûte pas la matrice : elle fait
échouer le validateur, l'exécution est gardée, et `replay --rescore` la renote
sans dépenser un jeton.

Ses tests tournent hors ligne et ne demandent aucun modèle :

```bash
cd validateurs && uv run --project .. python -m unittest test_issue1
```

## Modifier l'expérience

Copiez `scenarios/issue1-contexte.toml`, changez une configuration, relancez.
Vous n'aurez touché ni l'outil, ni le validateur, ni les autres configurations.

Le matériau de `briques/` est en revanche une entrée expérimentale : changer un
mot d'un prompt change la mesure et périme les tables déjà publiées. Ajoutez une
brique à côté et déclarez-la comme une cellule de plus, plutôt que de réécrire
celle qui a servi.

## Où aller ensuite

- [trysquare](https://github.com/AI-for-dev/trysquare) et sa [documentation](https://ai-for-dev.github.io/trysquare/), pour l'écriture d'un scénario
- [NÉON](https://github.com/AI-for-dev/neon), le dépôt mesuré, et son `ISSUES.md`
- [pi](https://pi.dev), le harnais mesuré
