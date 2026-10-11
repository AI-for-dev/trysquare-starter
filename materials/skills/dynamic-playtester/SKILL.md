---
name: dynamic-playtester
description: Transforme un bug de jouabilité d'un jeu d'arcade en tests rouges, à partir d'un catalogue de bugs connus du genre construit par recherche web. À utiliser quand un joueur rapporte un comportement anormal du jeu.
---

# Playtester dynamique

Un symptôme rapporté par un joueur n'est que le cas visible. Les jeux d'arcade cassent toujours aux mêmes endroits, et corriger le symptôme seul laisse passer ses voisins. Tu pars donc des bugs connus du genre, tu gardes ceux qui vivent dans le même composant que le symptôme, et tu écris un test **rouge** pour chacun. Tu ne corriges pas le jeu.

## 1. Catalogue

Le catalogue des bugs connus est `references/bugs-arcade.md`, dans le dossier de ce skill, avec une section `##` par genre de jeu.

Identifie le genre du jeu (README, code), en anglais (`shoot 'em up`, `platformer`, `maze game`...). Si le catalogue n'a pas de section pour ce genre, ou si l'utilisateur demande de le refaire, lance `bash scripts/catalogue.sh "<genre>"` depuis le dossier du skill. Le script fait la recherche web dans une session séparée qui ignore le bug, pour que le catalogue couvre tout le genre et pas seulement le symptôme. Il peut prendre plusieurs minutes : attends qu'il ait fini.

Lis ensuite la section du genre en entier.

## 2. Composant

Lis le code du jeu. Trouve la fonction qui produit le symptôme, et note comment un test peut l'atteindre par les fonctions exportées. Note dans quel ordre la boucle du jeu appelle ces fonctions à chaque tour. Si la logique vit dans une fonction de rendu, appelle-la avec un faux contexte de canvas, par exemple `new Proxy({}, { get: () => () => {} })`. Repère aussi la convention d'axes, et calcule à partir du code les valeurs limites que le jeu peut produire : vitesse maximale, `dt` plafonné, dimensions. Prends ces limites sur toute la partie (dernier niveau, difficulté maximale), pas seulement au départ. Note ces nombres, les tests s'y référeront.

## 3. Sélection

Prends dans le catalogue **toutes** les entrées du composant trouvé. Chaque test retenu doit faire agir la fonction trouvée à l'étape 2 sur les objets du symptôme. Il n'appelle une autre fonction exportée que si l'entrée l'exige (un déplacement, par exemple), et seulement après une première passe de la fonction du symptôme, dans l'ordre de la boucle : une correction écrite dans l'une ou l'autre fonction doit être jugée de la même façon. Une entrée qui porte sur un autre objet teste un autre bug : écarte-la. Écarte aussi les entrées qui décrivent une amélioration de gameplay plutôt qu'un défaut : l'invariant doit être une propriété que le joueur attend déjà du jeu. Ces cas viennent du catalogue et non des tickets ou des tests déjà présents dans le dépôt : c'est ce qui rend la démarche valable sur un jeu sans ticket détaillé.

Écris la liste avant de coder : pour chaque entrée, son invariant et pourquoi elle s'applique ici.

## 4. Tests rouges, un par un

Ajoute les tests à la fin du fichier de tests existant, un `describe` par entrée retenue, et un `test` par variante (chaque côté, chaque axe). L'outil `edit` exige toujours `path`.

Écris **un seul test à la fois**, et ne passe au suivant qu'une fois celui-ci rouge pour la bonne raison :

1. écris le test. Il commence par une **précondition** : une assertion qui calcule les bords des objets et vérifie qu'ils se chevauchent, ou se chevaucheront pendant le pas. Elle porte sur l'état que tu as écrit à la main, avant tout appel au code du jeu, et rien n'est vérifié entre deux appels : seul le résultat final compte, puisque la correction peut agir à n'importe quelle étape. Un bug « rien ne se passe » ressemble à un montage sans contact ; seule la précondition les distingue ;
2. en relisant le code actuel, écris en commentaire la valeur que l'assertion de l'invariant va recevoir aujourd'hui ;
3. `node --check <fichier>`, puis lance ce seul test (`node --test --test-name-pattern "<nom du test>" <fichier>`) ;
4. le test doit échouer sur l'assertion de l'invariant, avec la valeur prédite. Un échec sur la précondition, une autre valeur ou une autre erreur veut dire que le montage ne teste pas ce que tu crois : corrige-le avant d'aller plus loin. Un test qui passe déjà ne prouve rien.

Chaque test vérifié de cette façon sert de modèle au suivant.

Un test rouge n'a de valeur que s'il passe une fois le jeu corrigé, quelle que soit la correction raisonnable. Le montage doit donc n'admettre qu'**un seul** résultat correct :

- **isolé** : remplace les collections d'objets de l'état par un ou deux objets écrits à la main, loin des bords. Dans la scène du jeu, l'objet testé touche aussi des voisins et le résultat attendu devient ambigu ;
- **pénétration franche** : l'objet mobile entre de 2 ou 3 unités par le côté visé et nettement plus sur l'autre axe, pour que le côté touché ne fasse aucun doute. Un objet posé au centre d'un autre n'a pas de côté ;
- **axe témoin** : une vitesse non nulle sur l'axe qui ne doit pas changer, pour qu'une correction qui inverse tout échoue ;
- **atteignable** : seulement des positions et des vitesses que le jeu peut produire. Cite en commentaire la valeur limite calculée à l'étape 2 et montre que le montage reste en dessous ;
- **jugé de l'extérieur** : compare les bords des deux objets par un calcul explicite, et utilise les constantes de direction du jeu. Une fonction du code testé ne peut pas juger ce code.

Un cas symétrique fait exception à la pénétration franche et à l'axe témoin : un objet qui entre autant sur les deux axes n'a pas de côté ni d'axe témoin, et le seul résultat correct est symétrique lui aussi (les deux axes réagissent). Ce n'est pas un montage ambigu.

Avant d'écrire un cas, écris en commentaire la position de départ et le seul résultat qu'accepterait un jeu corrigé. Si tu en vois deux, change le montage. Commente aussi chaque `describe` en une ligne : l'invariant et l'entrée du catalogue.

## 5. Vérification

Lance la commande de test du projet. C'est fini quand chaque entrée retenue a ses tests, que les tests qui existaient avant passent toujours, et que chaque nouveau test échoue sur une `AssertionError`.

Termine par un tableau : entrée du catalogue, invariant, nom du test, raison de l'échec.
