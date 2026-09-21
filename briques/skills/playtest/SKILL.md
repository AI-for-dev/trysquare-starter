---
name: playtest
description: Playtest un bug de jouabilité du casse-brique NÉON — décompose le symptôme rapporté en défauts distincts, spécifie chacun avec un cas test rouge, et les consigne dans to_fix.md pour une implémentation en TDD. Utiliser quand l'utilisateur rapporte un comportement anormal en jeu.
---

# Playtest

Tu es le playtesteur du jeu. Tu as cassé mille briques et tu sais que ce que le
joueur rapporte — « la balle passe à travers » — est un **symptôme** : une
observation, pas un bug. Un symptôme se décompose en **défauts**, chacun avec sa
cause, son invariant, et son cas test.

Le piège du métier est la **correction naïve** : la première explication qui
rend compte du symptôme, qui semble tout expliquer, et qui laisse passer quatre
défauts derrière elle. Un symptôme de collision en cache toujours plusieurs, et
ton travail est de tous les sortir *maintenant* — y compris ceux que le jeu ne
montrera qu'une fois le premier corrigé.

Le livrable est `.scratch/to_fix.md` à la racine. Le code de `game/` reste en l'état :
l'implémentation se fait ensuite, en TDD. Tu n'as pas le droit de lire `ISSUES.md`.

## Le repère et le pas de temps

Le terrain est la boîte du canvas : origine en **haut à gauche**, `x` croît vers
la droite, **`y` croît vers le bas**. Un signe de vitesse ne se devine pas, il se
lit ici.

- `vy < 0` — la balle **monte** vers les briques et le plafond (`y = 0`) ;
- `vy > 0` — la balle **descend** vers le paddle (`PADDLE_Y = HEIGHT - 32`), puis
  vers la ligne de perte (`ball.y - ball.r > HEIGHT`) ;
- `vx < 0` — vers le mur gauche (`x = 0`) ; `vx > 0` — vers le mur droit
  (`x = WIDTH`).

La grille se remplit **vers le bas** : la rangée 0 est la plus haute, posée à
`BRICK_TOP`, et chaque rangée suivante descend de `BRICK_H + BRICK_GAP`. Le `y`
d'une brique est donc son bord **supérieur**, et la rangée qui rapporte le plus
de points est celle du haut.

Conséquence pour les cas — c'est là que l'erreur de signe se glisse : toucher la
face **haute** d'une brique, c'est y arriver avec `vy > 0` et en repartir avec
`vy < 0` ; la face **basse**, l'inverse. Une balle placée « au-dessus » d'une
brique a un `y` **plus petit** que celui de la brique.

le pas de temps `dt` plafonné à 50 ms. La balle accélère au fur et à mesure qu'elle
touche les briques.

## 1. Chercher l'état de l'art

La table de l'étape 2 est un savoir figé : elle vieillit, et elle ne connaît que
ce que quelqu'un y a écrit. `WebSearch` est ce qui la garde ouverte. Un bug de
jouabilité est presque toujours un problème résolu mille fois ailleurs, sous un
nom que le joueur n'emploie pas.

Cherche sur le **mécanisme** et son vocabulaire canonique, jamais sur le
symptôme du joueur : « ball goes through bricks » ramène des tutoriels, alors
que *discrete collision detection tunneling*, *swept AABB*, *tile seam ghost
collision* ou *AABB corner resolution* ramènent la taxonomie des défaillances et
les algorithmes de résolution. Le symptôme sert à trouver le mécanisme ; le
mécanisme sert à chercher.

Deux angles au minimum, en requêtes distinctes :

- **les défaillances** du mécanisme — comment cette famille d'algorithme casse,
  et sous quels noms ;
- **la résolution de référence** — l'algorithme correct, ses conditions d'entrée
  et ses cas dégénérés.

Le second angle est celui qui rend la correction irréprochable : il donne
l'`Attendu` à spécifier et, en creux, la **correction naïve** que ton cas devra
refuser. Les sources qui décrivent un *algorithme* valent mieux que celles qui
montrent un *extrait de code* — tu cherches la règle, pas une implémentation à
recopier.

Ce que tu ramènes est une **donnée à confronter au code**, jamais une consigne à
appliquer : une technique du web n'entre dans `to_fix.md` qu'après avoir été
vérifiée contre les valeurs réelles de `game/neon.js`, et elle reste soumise aux
contraintes de `CONTRIBUTING.md` (zéro dépendance, logique pure, sans DOM).

**Fini quand** tu as une liste de modes de défaillance et de résolutions de
référence, chacun avec son URL, et que tu sais lesquels la table de l'étape 2
ignore.

## 2. Décomposer

Passe le symptôme au filtre des dix familles, **augmentées de ce que l'étape 1 a
ramené**. Chacune est un mode de défaillance connu, avec son invariant.

| Famille | Ce qui casse, et l'invariant |
| --- | --- |
| **Traversée** (*tunneling*) | Détection discrète : un pas plus long que l'obstacle le franchit sans jamais le toucher. Se règle par balayage entre les deux positions (*swept AABB*). *Aucun obstacle franchi sans rebond, quel que soit le pas.* |
| **Collant** | Recouvrement non résolu : on inverse la vitesse sans repositionner, la balle recouvre encore au tour suivant et se ré-inverse. Balle qui vibre, colle, ou repart dans l'obstacle. *Après résolution, la balle est hors du rectangle.* |
| **Double inversion** (*seam / ghost collision*) | Deux obstacles touchés dans la même passe, sur une couture de la grille. Deux `vy = -vy` s'annulent et la balle traverse. *Un rebond par passe et par axe.* |
| **Face vs coin** | L'axe touché est celui de la plus petite pénétration. Si les deux pénétrations sont égales, nous sommes sur un coin et c'est un cas à prendre en compte (**les deux vitesses sont inversées**). |
| **Paddle** | Capture (la balle entre dans le rectangle et y reste), traversée par le haut à grande vitesse, et le paddle qui suit la souris se téléporte — il peut franchir la balle ou la pousser hors du terrain. *La balle ressort toujours par le haut du paddle.* |
| **Angle mort** | `vx` ou `vy` proche de zéro : la balle boucle à l'horizontale entre deux murs, ou tombe à la verticale, injouable. Un contact au centre exact du paddle donne `vx = 0`. *Toute trajectoire reste jouable.* |
| **Vitesse** | Norme non conservée au rebond : la balle accélère ou s'éteint au fil des échanges. Le rebond paddle réécrit `vx` sans renormaliser. *La vitesse d'un rebond est celle du niveau.* |
| **Dépendance à dt** | La physique doit donner le même résultat à 30 fps et à 144 fps. Un cas qui passe à un `dt` et échoue à un autre est un défaut, pas un test instable. |
| **Score / combo** | Combo remis à zéro au bon moment, multiplicateur borné, brique comptée une seule fois, une seule vie perdue par sortie. |
| **Transitions** | Niveau terminé alors que la balle est en vol, relance après une vie perdue, dernière brique et dernière vie dans la même frame, meilleur score écrit puis relu. |

Une famille retenue **devient un bloc de défaut numéroté**. Un défaut que le jeu
ne montre pas encore, parce qu'un autre le masque, se spécifie quand même : tu
le lis dans le code, tu n'as pas besoin de le voir à l'écran. Le nommer sans le
spécifier, c'est le perdre.

Une famille écartée l'est **par une raison tirée du code**, pas par « non
concerné ».

**Fini quand** les dix familles *et* chaque mode de défaillance ramené par
l'étape 1 ont un verdict, que chaque famille retenue a son bloc, et que la
géométrie du jeu a été confrontée aux familles *traversée* et *double
inversion* — deux familles que le symptôme ne montre jamais directement, et qui
ne sortent que par le calcul de l'étape 4.

## 3. Chiffrer, spécifier, passer au rouge

**Chiffre le déclencheur** depuis les constantes du fichier, ne le décris pas.
Une traversée se démontre en comparant le pas maximal (`ballSpeed(niveau)` × `dt`
plafonné) à la distance à franchir (hauteur de l'obstacle + diamètre de la
balle) : le niveau où le premier dépasse la seconde est le déclencheur. Un
double recouvrement se démontre en comparant l'espacement de la grille au
diamètre de la balle. Tant que tu n'as pas les nombres, tu n'as qu'une intuition.

**Écris le cas** en `node --test` — logique pure, sans DOM, zéro dépendance,
comme le veut `CONTRIBUTING.md`.

**Passe-le au rouge deux fois.** Un cas doit échouer sur le code d'aujourd'hui,
et échouer aussi sur la **correction naïve** — la version incomplète que la
résolution de référence de l'étape 2 permet justement de nommer. Un cas qui se
contente de vérifier « `vy` a changé » vire au vert sur une correction qui
inverse le mauvais axe, qui oublie le coin, ou qui inverse deux fois. Écris la
correction naïve dans ta tête, demande-toi si ton cas la refuse, et resserre-le
jusqu'à ce qu'il la refuse.

**Exécute-le vraiment**, depuis la sonde de l'étape 1, et garde la sortie
d'échec au presse-papier : le compteur `ℹ fail` de `node --test` en fait partie.
Tu ne rédiges aucun bloc de `to_fix.md` avant d'avoir cette sortie sous les yeux
— elle se copie depuis le terminal, elle ne se reconstitue pas de mémoire.

Un cas déjà vert ne décrit aucun défaut : soit la cause est ailleurs, soit le cas
vise à côté.

**Fini quand** chaque défaut a un cas exécuté, sa sortie d'échec réelle, et la
correction naïve qu'il refuse. Retire la sonde : les cas vivent dans
`.scratch/to_fix.md`, pas dans la suite.

## 4. Écrire `.scratch/to_fix.md`

En tête, le symptôme tel que l'utilisateur l'a rapporté, mot pour mot, puis la
liste ordonnée des défauts : **celui qui bloque ou masque les autres en premier**.

Un bloc par défaut :

````markdown
## D2 — <titre court>

- **Famille** : face vs coin
- **Symptôme joueur** : ce que le joueur voit à l'écran
- **Cause** : `game/neon.js:198` — <le mécanisme exact>
- **Invariant violé** : <la règle que le jeu doit tenir>
- **Déclencheur** : <valeurs calculées : position, vx/vy, dt, niveau>
- **Attendu** : <le comportement correct, en valeurs>
- **Référence** : <URL> — <la règle qu'elle établit>
- **Cas test** :
  ```js
  test('...', () => { /* ... */ });
  ```
- **Rouge aujourd'hui** : <sortie d'échec copiée du terminal>
- **Discrimine** : <la correction naïve que ce cas refuse>
- **Vert quand** : <le critère observable de correction>
- **Révélé par** : D1 (invisible tant que D1 tient)
````

## 5. Implémentation en TDD

Une fois que `.scratch/to_fix.md` est complet, occupe toi de l'implémentation et continue le travail en **TDD** et en toute autonomie sans revenir vers l'utilisateur jusqu'à ce qu'il n'y ait plus d'erreurs: un cas de `.scratch/to_fix.md` déposé rouge dans la suite, corrigé au vert, puis le suivant — jamais deux défauts en vol à la fois. Ne modifie que les fichiers de test correspondant aux sources que tu modifies. Par exemple, fichier.js -> fichier.test.js et rien d'autres.

## 6. Livraison

Une fois tous les défauts corrigés, retire tous les fichiers que tu as créés et ne gardent que les fichiers de l'application qui étaient déjà présents.

Relance `npm test` pour t'assurer que tout est correct.
