---
name: playtester
description: Transforme un bug de jouabilité d'un casse-brique (breakout) en tests rouges, à partir du catalogue des bugs connus du genre inclus dans ce skill. À utiliser quand un joueur rapporte un comportement anormal d'un casse-brique.
---

# Playtester casse-brique

Un symptôme rapporté par un joueur n'est que le cas visible. Les casse-briques cassent toujours aux mêmes endroits, et corriger le symptôme seul laisse passer ses voisins. Tu pars donc du catalogue ci-dessous, tu gardes les entrées qui vivent dans le même composant que le symptôme, et tu écris un test **rouge** pour chacune. Tu ne corriges pas le jeu.

## Catalogue des bugs connus

Chaque ligne est une cause relevée dans des discussions de développeurs. L'invariant est la propriété qu'un casse-brique correct respecte toujours : c'est lui que le test vérifie.

### Collision balle-brique

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Rebond sur le mauvais axe | une seule réponse pour toutes les faces (`vy = -vy`), ou axe déduit de la position du centre de la balle | une face latérale inverse `vx`, une face haute ou basse inverse `vy`, l'autre composante ne change pas | https://stackoverflow.com/questions/1561538 ; https://stackoverflow.com/questions/62994269 |
| Coin mal résolu | tests des arêtes en `else if` : une seule face est retenue au coin | quand la balle pénètre autant sur les deux axes, les deux composantes s'inversent | https://gamedev.stackexchange.com/questions/70887 |
| Balle collée dans la brique | la vitesse est inversée sans sortir la balle ; la collision est redétectée au pas suivant et la vitesse ré-inversée | après résolution, la balle est hors de la brique, en contact avec la face touchée | https://learnopengl.com/In-Practice/2D-Game/Collisions/Collision-resolution ; https://gamedev.stackexchange.com/questions/95817 |
| Double rebond sur la jointure de deux briques | chaque brique répond seule : deux briques touchées dans le même pas inversent deux fois la même composante | deux briques jointives forment une surface continue : un seul rebond par axe et par pas | https://stackoverflow.com/questions/38967446 ; https://github.com/bevyengine/bevy/pull/685 |
| Traversée à grande vitesse (tunneling) | test discret après déplacement : en un pas, la balle avance de plus que l'épaisseur de la brique plus son diamètre | aucune brique n'est franchie sans être touchée, à toute vitesse atteignable et au `dt` maximal | https://github.com/bevyengine/bevy/issues/1240 ; https://stackoverflow.com/questions/61804245 |
| Brique détruite qui reste active | la brique n'est pas retirée ou son état n'est pas testé | une brique détruite ne fait plus rebondir la balle et ne rapporte plus de points | https://developer.mozilla.org/en-US/docs/Games/Tutorials/2D_breakout_game_pure_JavaScript/Collision_detection |
| Rebond et destruction séparés | le rebond écarte la balle avant que la destruction ne teste le contact | un contact produit le rebond et la destruction dans le même traitement | https://forum.gdevelop.io/t/brick-breaker-breakout-collision-problem/32533 |

### Collision balle-raquette

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Balle qui traverse la raquette ou s'y colle par le bord | contact détecté sans repositionner la balle | après contact, la balle est au-dessus de la raquette et repart vers le haut | https://stackoverflow.com/questions/77262029 ; https://stackoverflow.com/questions/63037446 |
| Balle bloquée à l'horizontale | `vy` n'est pas réinversée, ou l'angle de sortie peut devenir plat | après un rebond sur la raquette, `vy` pointe vers le haut et n'est pas nulle | https://stackoverflow.com/questions/61485421 |
| Angle de sortie inversé | formule de l'angle écrite avec le mauvais signe | touchée à gauche du centre, la balle repart vers la gauche, et inversement | https://gamedev.stackexchange.com/questions/35134 |
| Raquette testée trop tard | le test balle-raquette est imbriqué dans le test « la balle a atteint le bas » | le contact avec la raquette est testé à chaque pas | https://stackoverflow.com/questions/41962633 |

### Murs

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Balle qui vibre contre un mur | rebond déclenché sans tester le sens de la vitesse | le rebond n'a lieu que si la balle va vers le mur ; ensuite la composante pointe vers l'intérieur | https://developer.mozilla.org/en-US/docs/Games/Tutorials/2D_breakout_game_pure_JavaScript/Bounce_off_the_walls ; https://stackoverflow.com/questions/42209048 |
| Rebond manquant sur un côté | comparaison asymétrique, rayon oublié d'un côté | les murs sont testés avec le bord de la balle (`x - r`, `x + r`, `y - r`) | https://stackoverflow.com/questions/29588091 |
| Sortie par un mur lors d'un double contact | la boucle s'arrête à la première collision du pas | toutes les collisions d'un même pas sont résolues | https://github.com/bevyengine/bevy/pull/685 |
| Balle perdue non détectée | test du bas absent, ou remise en jeu défectueuse | sous le bord bas, une vie est perdue et la balle repart de sa position initiale | https://stackoverflow.com/questions/44355463 |

### Pas de temps

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Vitesse dépendante du framerate | déplacement en pixels par frame | le déplacement vaut vitesse × `dt` | https://stackoverflow.com/questions/16554296 |
| Norme de la vitesse qui change | vitesse modifiée composante par composante, ou force ajoutée | un rebond change la direction, pas la norme de la vitesse | https://stackoverflow.com/questions/49639346 |

### Raquette et entrées

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Raquette qui sort de l'écran | borne calculée avec la hauteur, ou sur le centre | la position de la raquette reste dans `[0, largeur - largeur de la raquette]` | https://stackoverflow.com/questions/72641246 ; https://stackoverflow.com/questions/22902640 |
| Raquette qui dérive seule | pas de zone morte sur l'axe analogique | sans entrée, la raquette ne bouge pas | https://stackoverflow.com/questions/75048963 |
| Raquette saccadée au clavier | déplacement appliqué dans le gestionnaire d'événement, soumis à la répétition des touches | l'état des touches est lu à chaque pas de la boucle | https://stackoverflow.com/questions/64692791 |

### Score et état

| Bug | Cause | Invariant | Source |
| --- | --- | --- | --- |
| Brique comptée deux fois | la collision est signalée deux fois pour la même brique | une brique rapporte ses points et décrémente le compteur une seule fois | https://discussions.unity.com/t/is-it-possible-for-oncollisionenter-to-be-called-twice-for-the-same-collision/639691 |
| Score ou vies remis à zéro au niveau suivant | le changement de niveau réinitialise tout l'état | score et vies survivent au changement de niveau, seuls les briques et le combo repartent | https://agonzalezla.itch.io/brickburst/devlog/720248/v-0115-fix-player-scoring-errors |
| Combo jamais remis à zéro | remise à zéro oubliée sur les transitions | le combo repart de zéro à la perte de la balle et à chaque nouveau niveau | https://sbox.game/facepunch/breakout/source?file=Game%2FBreakoutGame.cs |

Si le symptôme ne correspond à aucune section, dis-le et décris l'entrée qui manque (bug, cause, invariant), sans lui attribuer de source.

## 1. Composant

Lis le code du jeu. Trouve la fonction qui produit le symptôme, et note comment un test peut l'atteindre par les fonctions exportées. Note dans quel ordre la boucle du jeu appelle ces fonctions à chaque tour. Si la logique vit dans une fonction de rendu, appelle-la avec un faux contexte de canvas, par exemple `new Proxy({}, { get: () => () => {} })`. Repère aussi la convention d'axes (sens de `y`), et calcule à partir du code les valeurs limites que le jeu peut produire : vitesse maximale de la balle, `dt` plafonné, dimensions de la balle, des briques, de la raquette et de l'écart entre briques. Prends ces limites sur toute la partie (dernier niveau, difficulté maximale), pas seulement au départ. Note ces nombres, les tests s'y référeront.

## 2. Sélection

Prends dans le catalogue **toutes** les entrées de la section du composant trouvé. Chaque test retenu doit faire agir la fonction trouvée à l'étape 1 sur les objets du symptôme. Il n'appelle une autre fonction exportée que si l'entrée l'exige (un déplacement, par exemple), et seulement après une première passe de la fonction du symptôme, dans l'ordre de la boucle : une correction écrite dans l'une ou l'autre fonction doit être jugée de la même façon. Une entrée qui porte sur un autre objet teste un autre bug : écarte-la. Ces cas viennent du catalogue et non des tickets ou des tests déjà présents dans le dépôt : c'est ce qui rend la démarche valable sur un jeu sans ticket détaillé.

Écris la liste avant de coder : pour chaque entrée, son invariant et pourquoi elle s'applique ici.

## 3. Tests rouges, un par un

Ajoute les tests à la fin du fichier de tests existant, un `describe` par entrée retenue, et un `test` par variante (chaque face, chaque axe). L'outil `edit` exige toujours `path`.

Écris **un seul test à la fois**, et ne passe au suivant qu'une fois celui-ci rouge pour la bonne raison :

1. écris le test. Il commence par une **précondition** : une assertion qui calcule les bords de la balle et de la brique et vérifie qu'ils se chevauchent, ou se chevaucheront pendant le pas. Elle porte sur l'état que tu as écrit à la main, avant tout appel au code du jeu, et rien n'est vérifié entre deux appels : seul le résultat final compte, puisque la correction peut agir à n'importe quelle étape. Un bug « rien ne se passe » ressemble à un montage sans contact ; seule la précondition les distingue ;
2. en relisant le code actuel, écris en commentaire la valeur que l'assertion de l'invariant va recevoir aujourd'hui ;
3. `node --check <fichier>`, puis lance ce seul test (`node --test --test-name-pattern "<nom du test>" <fichier>`) ;
4. le test doit échouer sur l'assertion de l'invariant, avec la valeur prédite. Un échec sur la précondition, une autre valeur ou une autre erreur veut dire que le montage ne teste pas ce que tu crois : corrige-le avant d'aller plus loin. Un test qui passe déjà ne prouve rien.

Chaque test vérifié de cette façon sert de modèle au suivant.

Un test rouge n'a de valeur que s'il passe une fois le jeu corrigé, quelle que soit la correction raisonnable. Le montage doit donc n'admettre qu'**un seul** résultat correct :

- **isolé** : remplace la grille de briques par une ou deux briques écrites à la main, loin des murs et de la raquette. Dans la grille, l'écart entre rangées est souvent plus petit que le diamètre de la balle : elle touche aussi les voisines et le résultat attendu devient ambigu ;
- **pénétration franche** : la balle entre de 2 ou 3 unités par la face visée et nettement plus sur l'autre axe, pour que la face touchée ne fasse aucun doute. Une balle posée au centre d'une brique n'a pas de face ;
- **axe témoin** : une vitesse non nulle sur l'axe qui ne doit pas changer, pour qu'une correction qui inverse tout échoue ;
- **atteignable** : seulement des positions, des vitesses et des dimensions que le jeu peut produire. Cite en commentaire la valeur limite calculée à l'étape 1 et montre que le montage reste en dessous ;
- **jugé de l'extérieur** : compare les bords de la balle et de la brique par un calcul explicite, et utilise les constantes de direction du jeu. Une fonction du code testé ne peut pas juger ce code.

Un coin fait exception à la pénétration franche et à l'axe témoin : une balle qui entre autant sur les deux axes n'a pas de face ni d'axe témoin, et le seul résultat correct est que les deux composantes s'inversent. Ce n'est pas un montage ambigu.

Avant d'écrire un cas, écris en commentaire la position de départ et le seul résultat qu'accepterait un jeu corrigé. Si tu en vois deux, change le montage. Commente aussi chaque `describe` en une ligne : l'invariant et l'entrée du catalogue.

## 4. Vérification

Lance la commande de test du projet. C'est fini quand chaque entrée retenue a ses tests, que les tests qui existaient avant passent toujours, et que chaque nouveau test échoue sur une `AssertionError`.

Termine par un tableau : entrée du catalogue, invariant, nom du test, raison de l'échec.
