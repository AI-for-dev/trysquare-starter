# Hypothèse : les leviers de contexte contre le rebond sur les briques

Déclarée avant de mesurer, et versionnée. Une hypothèse écrite après coup est une
conclusion déguisée, et l'intérêt de l'écrire est de rendre publiable un résultat
décevant plutôt que de le reformuler discrètement.

**État : le critère existe, et il n'est pas aveugle.** `rebond_briques` est une sonde,
`briques/sonde-fournie/sonde.test.js` : des tests `node:test` déposés dans une copie de l'arbre de
l'agent faite hors du clone, qui posent une balle déjà en recouvrement avec une brique par
la face visée, appellent `frame()`, et exigent que la composante de vitesse de l'axe touché
s'inverse pendant que l'autre reste telle quelle. La composante hors axe est non nulle
dans chaque cas, faute de quoi une correction qui inverse les deux axes à tout hasard
passerait pour une correction par face.

Une colonne l'accompagne, de la même exécution. `rebond_angles` joue le coin de la brique,
où la balle arrive par la diagonale et où les deux composantes doivent s'inverser. Elle est
plus dure que `rebond_briques` et non un cas à part : une correction qui compare les deux
pénétrations et n'en inverse qu'une passe les quatre faces et échoue au coin.

Une troisième colonne a existé et a été retirée. `rebond_domaine` jouait les murs du champ
comme garde de régression, mais ils rebondissent déjà à l'étalon : la colonne était verte
partout, y compris sur les exécutions qui n'avaient rien livré, et ne séparait donc aucune
cellule. Une garde de régression a sa place dans la suite du dépôt, pas dans le critère
d'une mesure.

Vérifiée sur sept arbres. L'étalon marque 0/5. Une correction par face 4/5, le coin étant ce
qui lui manque ; la même en traitant les pénétrations égales comme un coin, 5/5, ce qui dit
que la colonne est atteignable. « Inverse toujours vy » 2/5, « inverse les deux axes » 1/5 -
ce dernier ne gagne que le coin, ce qui est exactement le propos de la colonne. Restent la
correction par face extraite dans un `brickHit()` appelé depuis `step()`, 4/5 en disant sa
provenance sur chaque cas, et un arbre où `frame` a été renommée, qui ne rend aucun cas mais
la raison de son silence.

## Quatre colonnes de plus, et ce qu'elles doivent donner

Ajoutées après la rédaction de ce qui précède et **avant toute mesure de la matrice élargie**,
à partir du catalogue des bugs classiques du casse-briques : le rebond collant, la double
réflexion, le tunneling, la raquette. Deux d'entre elles serrent la correction demandée de plus
près, les deux autres constatent un bug latent que le ticket ne nomme pas. Les prédictions
sont écrites ici pour que la lecture d'après-mesure ne soit pas une reformulation.

`rebond_sortie` exige que la balle soit ressortie du rectangle de la brique, ce qui est la
seconde moitié de la correction que le commentaire du dépôt décrit. **Prédiction : elle suit
`rebond_briques` de près mais reste en dessous**, parce que le commentaire nomme les deux
moitiés dans la même phrase et qu'une correction guidée par lui devrait les faire toutes les
deux, mais qu'inverser une vitesse est le geste qui vient en premier à l'esprit. L'écart entre
les deux colonnes est la mesure de combien de corrections s'arrêtent à mi-chemin.

`rebond_voisines` joue une couture de la grille, où la balle recouvre deux briques à la fois.
**Prédiction : bruitée et non monotone avec les leviers.** Elle ne dépend pas de la qualité du
raisonnement mais de la forme écrite - un `vy = -vy` s'annule au second tour, un
`vy = Math.abs(vy)` non, et une correction qui repositionne sort la balle du recouvrement avant
la seconde brique et passe sans même y penser. Un levier de contexte n'a aucune raison de
déplacer ce choix-là, donc une corrélation nette avec les cellules serait plus surprenante que
son absence.

`rebond_traversee` demande une détection continue. **Prédiction : noire sur les 200 exécutions.**
Aucun ticket ne mentionne la vitesse de la balle, le bug ne se voit qu'au niveau 6, et le
corriger demande de remplacer la détection plutôt que de la compléter.

`rebond_raquette` joue trois défauts de `step()` que personne n'a demandé de corriger.
**Prédiction : noire sur les 200 exécutions**, et pour une raison plus forte que la précédente :
même un agent qui les remarquerait sortirait du périmètre en les corrigeant, et le ticket cadré
l'interdit explicitement. Si cette colonne s'allumait quelque part, il faudrait lire `in_scope`
sur la même ligne avant d'y voir une réussite.

Les deux dernières sont donc gardées en sachant qu'elles ne sépareront rien. Elles ne portent
aucun verdict, et le seul énoncé qu'elles produiront - « personne n'est allé au-delà de ce que
le ticket nommait » - vaut d'être établi plutôt que supposé.

### L'étalon a bougé entre deux matrices, et il faut le lire avant tout le reste

Écrit après coup, comme les sections de réponse qui suivent, et placé avant elles parce
qu'il conditionne ce qu'on a le droit d'en tirer.

Deux campagnes de ce scénario ont été archivées, à deux jours d'intervalle. Elles déclarent
le même `etalon = "etalon-v1"` et **n'ont pas mesuré le même dépôt** :

| matrice | `etalon_commit` | le commit |
| --- | --- | --- |
| `…_ilaas_gemma-4-31b_n20`, 6 août | `144675b9` | *feat: neon glow pass* |
| `…_opencode-go_deepseek-v4-flash_n20`, 8 août | `d62ccd1f` | *update issue.md* |

Le tag a été déplacé entre les deux. Ce que le déplacement emporte n'est pas cosmétique :
`git diff` entre les deux commits touche deux fichiers, et l'un est `ISSUES.md`, dont
**l'issue #1 est entièrement réécrite**. La version qu'a lue la matrice gemma ne décrivait
que le rebond par face. Celle qu'a lue la matrice deepseek nomme en plus le coin (« equal
penetrations means a diagonal hit - flip both components »), la sortie du rectangle, la
couture de la grille et le tunneling, ce dernier chiffré. L'autre fichier est `game/neon.js`,
qui exporte désormais `frame`.

La conséquence porte directement sur la prédiction 2 de ce fichier. `+well_crafted` donne
`rebond_angles` 0/20 sur gemma et 19/20 sur deepseek, à fichier de prompt rigoureusement
identique : ce n'est pas le prompt qui a changé, c'est le document qu'il désigne. Mais le
modèle, le fournisseur et le ticket ont changé ensemble, donc **aucune attribution n'est
possible entre ces deux matrices**, et le seul énoncé qu'elles autorisent à deux est
« elles ne se comparent pas ».

Deux choses à en retenir, et la seconde est la plus utile.

D'abord que la garde dont ce dispositif se réclame - « un tag, cloné, jamais l'arbre de
travail » - **ne suffit pas**. Un tag est un pointeur mobile, et `git tag -f` ne laisse
aucune trace côté mesure. Ce qui l'a rattrapé est `etalon_commit`, archivé par run, dont le
docstring de `trysquare/repo.py` disait déjà qu'il est « the only trace left when a tag is
moved between two matrices ». La correction est en amont : un étalon peut désormais être un
commit écrit en entier, qui ne bouge pas.

Ensuite, et c'est la troisième fois dans l'histoire de ce scénario, que **ce qui a failli
devenir une conclusion était un incident que l'archive savait nommer** - après la colonne
des reprises et après `suite_lancee`. Aucune des trois n'était dans une table.

L'archive du 6 août est conservée sous `results/issue1-contexte_etalon-v1-at-144675b9_…`,
son nom disant le commit puisque son tag ne le dit plus. Elle ne se rejoue par le chemin
normal qu'avec un clone local où `etalon-v1` est remis sur `144675b9`.

### Un défaut de `suite_lancee`, le comparateur cette fois

Distinct de celui de la section suivante, et trouvé sur la matrice deepseek : la colonne y
valait 0/20 dans les neuf cellules alors que les 180 exécutions avaient lancé la suite.

`LANCEMENTS` était une liste de **chaînes exactes**, au motif défendable qu'un motif décide
à l'avance de ce qu'on n'a pas encore vu là où une liste se complète en regardant ce que les
agents ont tapé. L'argument était juste et la conclusion fausse : ce qui varie d'un modèle à
l'autre n'est pas quelle commande lance la suite, c'est ce que l'agent met autour.
`deepseek-v4-flash` préfixe du répertoire de travail (`cd …/repo && npm test`, 664 fois) et
redirige la sortie (`npm test 2>&1 | tail -30`, 80 fois) ; `gemma-4-31b` tape `npm test` nu.

La reconnaissance est passée au motif, et le risque inverse - compter une mention pour un
lancement - a été cherché sur les 360 exécutions archivées : six commandes contiennent la
chaîne sous une forme non exécutante, et toutes les six enchaînent un vrai lancement dans la
même ligne.

Ce qui a rendu le défaut visible est la raison attachée au faux, qui recopie les commandes
non reconnues : elle affichait un `npm test` dans la liste des commandes « où aucun lancement
n'a été trouvé ». Une métrique qui dit faux sans dire pourquoi aurait tenu une campagne
entière.

### Ce que la mesure a répondu

Cette section porte sur une matrice **retirée depuis** de `results/`, dont les noms de
cellules (`rien`, `+règle`, `+ticket cadré`, `pile soignée`) et la colonne `rebond_raquette`
n'existent plus. Elle est gardée telle quelle : c'est ce qui avait été écrit au vu de ces
chiffres-là, et la réécrire à la lumière des suivants ferait exactement ce que ce fichier
existe pour empêcher.

Les quatre prédictions ci-dessus ont été écrites avant de mesurer, puis tranchées sans dépenser
un jeton : `trysquare replay --rescore` rejoue le validateur sur les 240 arbres archivés de
`results/…_n20`, et la sonde élargie tourne sur eux comme elle aurait tourné le jour même. Les
prédictions ne sont pas retouchées ; ce paragraphe est ajouté sous elles.

| cellule | briques | sortie | voisines | traversee | raquette |
| --- | --- | --- | --- | --- | --- |
| rien | 12/20 | 12/20 | 8/20 | 0/20 | 0/20 |
| +thinking | 19/20 | 18/20 | 17/20 | 0/20 | 0/20 |
| +règle | 11/20 | 7/20 | 6/20 | 0/20 | 0/20 |
| +ticket cadré | 18/20 | 17/20 | 15/20 | 0/20 | 0/20 |
| -prompt système | 15/20 | 11/20 | 9/20 | 0/20 | 0/20 |
| pile soignée | 20/20 | 20/20 | 20/20 | 0/20 | 0/20 |

**`rebond_sortie` : prédiction tenue.** Elle suit `rebond_briques` et reste en dessous partout
sauf dans la cellule de base, où les douze corrections justes repositionnaient déjà. L'écart se
creuse là où la correction est la moins guidée - `+règle` perd 4 corrections sur 11,
`-prompt système` 4 sur 15 - et disparaît sur `pile soignée`. C'est exactement la colonne qu'on
espérait : elle distingue une correction complète d'une correction à mi-chemin, et elle le fait
sur des cellules que `rebond_angles` ne sépare pas du tout.

**`rebond_voisines` : prédiction fausse, et c'est le résultat le plus intéressant.** Elle avait
été annoncée bruitée et non monotone, au motif que la forme écrite (`-vy` contre `Math.abs`) ne
dépend pas des leviers. Elle est en fait strictement monotone avec eux, et ordonne les cellules
comme `rebond_briques` en les écartant davantage : 8/20 à la base contre 20/20 sur la pile
soignée, là où le critère ne va que de 12 à 20. L'explication tient à `rebond_sortie` : une
correction qui repositionne sort la balle du recouvrement avant d'atteindre la seconde brique et
passe sans avoir rien prévu pour elle. `voisines` mesure donc en grande partie la même chose que
`sortie`, plus sévèrement. Deux colonnes plutôt qu'une reste justifié - elles se séparent de 4
runs sur la base et de 4 sur `-prompt système` - mais elles ne sont pas indépendantes, et une
lecture qui les traiterait comme deux confirmations distinctes compterait deux fois.

**`rebond_traversee` et `rebond_raquette` : prédictions tenues, 0/240 l'une et l'autre.**
L'énoncé qu'elles existaient pour établir est établi.

### Un défaut de `suite_lancee` que ce rejeu a mis au jour

Il ne concerne pas les quatre colonnes ajoutées, et rien dans l'élargissement de la sonde ne
touche cette métrique : toutes les colonnes d'avant sont identiques au bit près, sauf celle-ci.
`suite_lancee` ne retombe pas sur ses valeurs archivées - `+thinking` 11 puis 7, `+règle` 18
puis 12 - et **ce sont les valeurs archivées qui sont fausses.**

La session archivée est l'enregistrement de ce que l'agent a fait, et les deux formes sous
lesquelles elle est conservée concordent : le `session/*.jsonl` et la charge base64 du
`session/*.html` donnent les mêmes appels. Notées contre elle, les 240 exécutions donnent
240/240 d'accord pour le rejeu et 230/240 pour l'archive. Les dix écarts vont tous dans le même
sens - l'archive affirme un `npm test` que l'agent n'a pas lancé - et se trouvent tous dans
`+règle` (6) et `+thinking` (4), c'est-à-dire les deux cellules dont le ticket ne nomme pas la
commande. Sur `ab8180eb`, l'agent a fait trois appels (`ls -R`, `read game/neon.js`, `edit`) et
la chaîne `npm test` n'apparaît **pas une seule fois** dans sa session, alors que l'archive la
donne comme raison.

La cause est écrite dans `trysquare/assay.py`, au docstring de `tool_calls()` : la version de
ce validateur qui a mesuré la matrice lisait `context["trace"]`, le flux brut, et recollait les
appels par `toolCallId`. Ce fichier a depuis été repris sur la base, qui lit la **session** -
« the `toolCallId` reconciliation that file needed had no cause but reading the wrong file ».
La trace n'est délibérément pas archivée, cinq cents fois la taille pour rien que le relevé
par message ne dise déjà, si bien que le `trace` que `context.json` liste encore pointe vers un
répertoire de travail purgé. Par quel chemin exactement ce flux produisait un `npm test`
fantôme n'est donc plus vérifiable, et n'a pas à l'être : la question « qu'a fait l'agent » se
lit dans la session, et c'est ce que le code lit aujourd'hui.

Un second symptôme du même défaut, sans conséquence sur les verdicts : la raison de
`skill_invoque` annonçait un nombre d'appels d'outil gonflé sur 120 des 197 exécutions où elle
est comparable (7 contre 3, 11 contre 5). Le booléen, lui, est identique partout.

**Conséquence pratique.** La colonne `suite_lancee` de `results/…_n20/synthesis.md` ne doit pas
être citée en l'état. Elle se corrige sans dépenser un jeton par un `trysquare replay --rescore`,
qui du même geste ajoute les quatre colonnes ci-dessus - et remesurer la matrice, ce que
l'élargissement demandait déjà, règle la question au passage.

**Ce qui doit être dit avant de lire quoi que ce soit dans cette matrice.** La forme de
la sonde a été choisie *après* qu'une première matrice a tourné. Ses six exécutions ont
toutes été invalides - le validateur était encore un squelette et refusait de noter -
mais leurs diffs ont été lus pour trancher la question que ce fichier laissait ouverte,
et le compte est net : trois corrections sur cinq sont restées dans `frame()`, qui n'est
ni exportée ni appelable sans canvas, et les deux qui en sont sorties dans une fonction
exportée sont les deux cellules les mieux outillées. Une sonde limitée aux exports
aurait donc noté « a extrait une fonction » sous le nom de `par_face`, et son
atteignabilité aurait corrélé avec le traitement. D'où la copie instrumentée, qui
exporte tout ce que le module déclare au premier niveau et atteint la correction où
qu'elle ait atterri.

Ce choix est donc informé par des données, et le dire est le seul moyen de ne pas le
faire passer pour une décision prise à l'aveugle. Ce qu'il n'a pas touché : aucune des
prédictions ci-dessous n'a été relue ni retouchée depuis, et la sonde ne connaît que la
géométrie du rebond, jamais la cellule qui l'a produit.

## Pourquoi cette tâche plutôt que l'issue #2

Le banc du module 2.1 mesurait l'issue #2, et il finit par admettre que la moitié
du ticket qui décide si le travail est fait - « arrêter de scanner toutes les
briques » - n'a pas de forme mécanique. Elle a été approchée par un motif dans le
diff, le motif s'est trompé deux fois, et le module conclut qu'il faut un juge.

L'issue #1 est d'une autre nature. Sa moitié dure est un **comportement** : un
choc sur le haut ou le bas d'une brique inverse `vy`, un choc sur un côté inverse
`vx`. Un comportement s'exécute au lieu de se reconnaître, donc le critère peut
être une sonde plutôt qu'un motif, sans juge et sans jetons.

La moitié facile, elle, est que la balle cesse de traverser les briques, ce qu'une
seule ligne obtient (`ball.vy = -ball.vy`). La tâche conserve donc la propriété
dont le module a besoin - une exécution peut paraître terminée alors que la moitié
du ticket n'est pas faite - et gagne un critère qu'on n'a pas à croire sur parole.

## Ce qui est prédit

1. **La base livre la moitié facile et pas la moitié dure.** N'importe quel rebond
   supprime le symptôme le plus visible, et rien dans une demande vague ne pointe
   vers le cas latéral.
2. **Nommer le ticket déplace la moitié dure.** Le mécanisme est écrit dans
   `ISSUES.md`, sous l'issue #1, dans le dépôt que l'agent a déjà sous la main. Le
   ticket cadré ne le recopie pas : il nomme l'issue, le périmètre et le critère
   d'arrêt. Ce qui est mesuré est donc si pointer un matériau écrit suffit à ce
   qu'il soit lu, pas si un agent sait suivre une consigne qu'on lui tend.
3. **La règle de projet ne déplace pas la moitié dure.** `briques/AGENTS.md` ne dit
   rien de ce ticket. Sa cellule est un témoin : si elle déplace le critère, alors
   le critère capte de la diligence générale et non le levier que la ligne nomme.
4. **Le débordement est plus mince ici que sur l'issue #2, et pourrait ne rien
   discriminer.** Avec l'issue #1 comme tâche, la signature de l'issue #1 devient le
   travail demandé et quitte l'ensemble du débordement. Il ne reste que l'issue #6,
   seule, ce qui est exactement la situation contre laquelle
   `scripts/banc/signatures.py` met en garde dans ses propres commentaires.
5. **La compétence déplace la moitié dure au-delà de la pile soignée.** C'est la
   prédiction que la cellule `pile soignée +skill` existe pour tester, et elle est la
   plus fragile de cette liste. Le raisonnement : le rebond par face est un
   comportement, et écrire le cas limite avant la correction force à formuler ce que
   le code doit faire face par face, ce qu'une correction écrite d'abord n'oblige pas.
   La compétence ne nomme pas ce mécanisme - elle dit de chercher le cas d'égalité
   entre deux grandeurs comparées et de vérifier ce qui ne doit pas changer -, donc si
   l'écart existe, il vient d'une méthode et non d'un indice.

   Sa comparaison est **`pile soignée`, pas `rien`.** C'est la seule cellule dont elle
   ne diffère que par la compétence ; l'écart au verdict, qui se prend contre `rien`,
   mélangerait les quatre leviers de la pile avec celui-ci.

   Ce qui la réfuterait, en propre : les deux piles rendent le même
   `rebond_briques`. Alors la compétence produit du travail de test sans produire de
   comportement, ce qui est un résultat publiable et pas un ratage de la brique - et
   `tests_ajoutes` le dira, en montrant qu'elle a bien été employée.

   **`skill_invoque` se lit avant tout le reste de cette ligne.** Elle dit si l'agent est
   allé lire le corps du `SKILL.md`, ce que pi laisse à sa discrétion : seuls le nom et la
   description entrent dans le prompt système. Rien de ce qui précède n'est affirmé sur les
   exécutions où elle est fausse - une brique jamais ouverte ne mesure pas une méthode de
   travail, elle mesure ce que sa description a réussi à déclencher, et ce serait un autre
   résultat qu'il faudrait écrire dans ces termes.

## Ce qui la réfuterait

- La base atteint la moitié dure aussi souvent que le ticket cadré. Alors le critère
  n'est pas difficile et ne discrimine rien.
- Aucune cellule n'atteint la moitié dure. Alors le critère est saturé à zéro, la
  matrice ne dit rien, et l'honnêteté est de l'écrire plutôt que de chercher ensuite
  une mesure plus complaisante.
- La cellule `+règle` déplace le critère autant que la cellule `+ticket cadré`. Alors
  le critère mesure de la diligence, et tout ce que ce fichier affirme sur les
  tickets est sans support.
- La colonne `sonde_atteinte` n'est pas pleine. Elle dit si la sonde a vu la balle
  toucher la brique, et sa raison d'être est cette clause : tant qu'elle est vraie
  partout, `par_face` mesure bien « l'agent a-t-il fait la moitié dure ». Dès qu'elle
  se creuse, le critère glisse vers « l'agent a-t-il fait la moitié dure **à un endroit
  atteignable** », ce qui est une autre affirmation et doit être écrite dans ces termes
  dans la synthèse. C'est la copie instrumentée qui la maintient pleine, et non une
  propriété du dépôt : elle se creusera le jour où une correction cessera de passer par
  `step()` puis `frame()`.

## La cellule `pile soignée +sonde`, et ce qu'elle doit donner

Ajoutée après tout ce qui précède et **avant toute mesure la comportant**. Elle pose la
question inverse de toutes les autres : ailleurs on donne du contexte et on regarde si
l'agent trouve le cas que la demande ne nomme pas ; ici on lui donne le test qui le juge,
rouge, dans l'arbre, et on regarde s'il se corrige. Une brique `kind = "files"` dépose
`briques/sonde-fournie/sonde.test.js` en `game/sonde.test.js` avant que l'agent démarre.

Elle se lit contre `pile soignée`, la seule cellule dont elle ne diffère que par cette
brique.

La sonde fournie est le fichier même qui note - une seule source, dont `issue1.py` réécrit la
seule ligne d'import pour sa copie de notation. Cette cellule lit donc aussi les deux groupes
latents, tunneling et raquette, que l'issue #1 ne commande pas : elle peut les faire passer là
où les autres cellules ne les voient jamais, si bien que ces deux colonnes ne se comparent pas
d'une cellule à l'autre. Les quatre premières, si.

Elle importe `frame` depuis `./neon.js`, que le module n'exporte pas : à l'arrivée la suite est
donc rouge au chargement, et la première chose à faire est d'exporter la boucle de rendu. C'est
vérifié - 15 rouges et les 6 cas du dépôt verts à l'étalon, 21 verts sur un arbre corrigé.

1. **`rebond_briques`, `rebond_sortie` et `rebond_voisines` montent à 20/20 ou tout près.**
   C'est la prédiction molle, et elle serait presque une tautologie si la cellule était
   comparée à `rien` : `pile soignée` y est déjà à 20/20 sur les trois. Ce qui se mesure ici
   est donc le contraire d'un gain - **si la cellule descend en dessous de `pile soignée`,
   c'est le résultat**, et il dirait que recevoir un test rouge détourne le travail de la
   correction vers la satisfaction du test.
2. **`rebond_angles` est la colonne où quelque chose peut se passer.** C'est la seule que la
   pile soignée ne sature pas, la sonde fournie la nomme explicitement (le coin, les deux
   composantes), et un agent qui exécute le test avant de conclure ne peut pas s'arrêter à
   une correction par face. Prédiction : elle monte, et c'est le seul écart de cette cellule
   qui vaudra d'être cité.
3. **`sonde_intacte` est vraie partout, mais c'est la colonne à lire en premier.** Desserrer
   l'assertion est la réponse qui ne coûte rien, la notation ne s'y laisse pas prendre
   puisqu'elle réécrit sa propre copie, et une seule exécution qui l'a tentée change la
   lecture de toute la colonne des rebonds. Prédiction : 5/5 - un modèle de cette taille n'a
   aucune raison de préférer réécrire un test à corriger quatre lignes - et une infirmation
   est plus intéressante que la confirmation.
4. **`in_scope` baisse.** La sonde fournie n'est pas dans le périmètre - elle est donnée pour
   être lue et satisfaite - donc toute exécution qui y touche en sort. Une baisse ici n'est
   pas une indiscipline mais l'effet mécanique d'avoir mis un fichier de plus dans l'arbre,
   et c'est `sonde_intacte` qui dira laquelle des deux lectures s'applique. Écrit avant la
   mesure pour ne pas être choisi après elle.
5. **`tests_ajoutes` baisse aussi, et pour une raison qui n'est pas un manquement.** Le
   ticket demande les cas limites « d'abord en tests rouges, puis verts » ; un agent qui les
   a déjà sous les yeux n'a aucune raison d'en réécrire dans `game/neon.test.js`, que la
   métrique est seule à compter. Une cellule à `0/5` ici aurait fait exactement ce qu'on lui
   demandait.

## Ce qui n'est pas affirmé

Rien sur le coût. Jetons, tours et durée sont rapportés, mais une reprise rejoue
tout le contexte accumulé, donc une colonne de coût n'est lisible que lorsque les
reprises sont proches de zéro dans les cellules comparées.

Rien sur le périmètre de la cellule à compétence. `in_scope` est calculé contre deux
fichiers, `game/neon.js` et `game/neon.test.js`, et une compétence qui parle de tests
peut faire créer un fichier de test de plus. Un `in_scope` plus bas sur cette cellule
dira que la brique déplace l'endroit où les tests sont écrits, ce qui n'est ni une
défaillance du validateur ni un manque de diligence de l'agent. Cette lecture est
écrite ici avant la mesure pour ne pas être choisie après elle.

Rien entre les deux matrices de modèles. Le modèle est une constante de scénario
dans cet outil, donc la moitié « gros modèle » du 2×2 est une expérience distincte.
Durées et coûts ne se comparent qu'à l'intérieur d'une même matrice.

## Passes de fumée

Une exécution à `--repetitions 2` **n'est pas** un test de cette hypothèse et
aucune conclusion n'en sort. Elle sert à vérifier que le harnais est branché :
chaque exécution valide, les sorties complètes, et le niveau de raisonnement
enregistré par chaque session égal à celui que sa cellule déclare.
