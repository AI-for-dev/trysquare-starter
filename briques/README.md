# briques

Ce qu'un scénario injecte dans le clone ou passe à l'agent, un fichier par pièce.

Ces fichiers ne sont pas de la documentation. Les prompts, l'`AGENTS.md` et le
prompt système minimal sont des entrées expérimentales : changer un mot change
la mesure et périme les tables déjà publiées. Si une formulation doit
évoluer, créez une brique à côté et déclarez-la comme une cellule de plus, plutôt
que de réécrire celle-ci.

| fichier | ce que c'est |
| --- | --- |
| `issue1-simple-prompt.md` | la tâche de base : une demande réelle mais négligée |
| `issue1-well-crafted-prompt.md` | le même travail, demandé correctement, avec un pointeur vers `ISSUES.md` |
| `issue1-simple-prompt-with-skill.md` | la demande négligée, plus l'invocation de la compétence |
| `AGENTS.md` | une convention de projet, en fichier de contexte permanent |
| `SYSTEM-minimal.md` | le prompt système de l'agent réduit à trois lignes |
| `skills/playtest/` | une compétence : jouer le jeu avant de corriger, et chercher les cas limites |
| `sonde-fournie/sonde.test.js` | la sonde de notation, déposée dans l'arbre des deux cellules `add_tests` |

Le prompt cadré ne recopie pas le mécanisme du rebond, alors que `ISSUES.md` le
détaille dans le dépôt mesuré. Cette retenue est le sujet de la cellule : ce qui
est mesuré est si pointer un document écrit suffit à ce qu'il soit lu, et non si
un agent sait appliquer un indice qu'on vient de lui tendre.

La sonde est un seul fichier pour deux emplois : `validateurs/issue1.py` la
dépose dans une copie de l'arbre mesuré pour noter toutes les cellules, et la
brique `kind = "files"` du scénario la commite dans le clone des deux cellules
`add_tests` avant que l'agent démarre. La seule ligne qui sépare les deux usages
est son import, que le validateur réécrit dans sa copie.
