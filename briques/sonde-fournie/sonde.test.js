// sonde.test.js - les cas limites de l'issue #1, en tests exécutables, **donnés d'avance**.
//
// Ce fichier n'existe pas à l'étalon. Une brique `kind = "files"` du scénario le dépose dans
// l'arbre mesuré avant que l'agent démarre, et le commite sur l'étalon : la cellule qui le
// reçoit commence donc son travail avec la suite rouge et la spécification sous les yeux.
// C'est tout ce que cette cellule mesure - un modèle qui a déjà les tests qu'il faut
// se corrige-t-il ?
//
// ---------------------------------------------------------------------------
// CE QU'IL FAUT FAIRE POUR QUE CE FICHIER PUISSE SEULEMENT TOURNER
//
// Il importe `frame` depuis `./neon.js`, que le module **n'exporte pas** aujourd'hui. Tant
// que ce n'est pas le cas, `npm test` échoue au chargement du module et aucun cas ne joue.
// Exporter la boucle de rendu est donc la première chose à faire, et c'est une ligne.
// ---------------------------------------------------------------------------
//
// Quinze cas, en six groupes. Les quatre premiers sont l'issue #1, du plus grossier au plus
// fin, et chacun noircit une forme de correction incomplète que le précédent laissait passer :
//
//   `brique`   les quatre faces : l'axe touché s'inverse, l'autre ne bouge pas.
//   `angle`    le coin : les deux composantes s'inversent. Une correction par face échoue ici.
//   `sortie`   la balle est ressortie du rectangle. C'est la seconde moitié de ce que le
//              commentaire de `neon.js` décrit lui-même : « plus pushing the ball back out of
//              the brick ». Une correction qui inverse sans repositionner laisse le rebond
//              collant - au tour suivant la balle recouvre encore et se ré-inverse.
//   `voisines` deux briques touchées dans la même passe : le rebond s'applique une fois et pas
//              deux. Un `vy = -vy` appliqué deux fois s'annule et la balle traverse. Le gap de
//              la grille est de 8 px et le diamètre de la balle de 14, donc toute couture de la
//              grille est un double recouvrement : c'est le cas courant, pas la curiosité.
//
// Les deux derniers sont **d'autres bugs que l'issue #1 ne mentionne pas**, trouvés en écrivant
// les cas ci-dessus. Ils sont ici parce qu'ils vivent dans la même détection de collision et
// qu'un fichier de cas limites qui les taît serait mensonger, pas parce que le ticket les
// commande :
//
//   `traversee` la balle rapide saute par-dessus la brique sans jamais la toucher. La détection
//               est discrète : elle échantillonne la position avant et après le déplacement, et
//               à la vitesse du niveau 6 le déplacement d'une frame dépasse la hauteur d'une
//               brique. Seule une détection continue - un balayage entre les deux positions -
//               fait passer ce cas.
//
// Ce sont des tests `node:test` ordinaires, comme `game/neon.test.js`, lancés par la commande
// de `npm test`. Rien ici n'est une convention du harnais.

import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

// Un import, et non un `typeof` sur chaque nom : si l'un d'eux manque, le module ne se lie
// pas, aucun cas ne tourne, et l'échec dit *quel* nom manquait. C'est le bon message.
import {
  frame,
  step,
  createState,
  ballSpeed,
  WIDTH,
  HEIGHT,
  BALL_R,
  BRICK_W,
  BRICK_H,
  BRICK_GAP,
} from './neon.js';

// Le pas de temps d'une frame nominale, et le plafond que `boot()` applique sur une frame qui a
// bégayé. Les quatre premiers groupes n'en ont pas besoin - leur balle est déjà en recouvrement -
// mais `traversee` juge la détection *pendant* le déplacement, et c'est
// exactement ce que ces deux valeurs-là produisent dans le jeu.
const DT = 1 / 60;
const DT_MAX = 0.05;

// Chaque cas des quatre premiers groupes pose une balle **déjà en recouvrement** avec la brique,
// de 3 px par la face visée et de 17 px ou plus par l'autre axe. Rien n'avance d'un pas de temps
// pour *atteindre* la brique, donc rien ne dépend d'un `dt`. La vitesse hors axe est petite mais
// non nulle, pour qu'une correction qui inverse les deux axes à tout hasard échoue au lieu de
// passer.

describe('brique', () => {
  test('flanc gauche: la balle repart vers la gauche', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 96, y: 110, r: BALL_R, vx: 300, vy: 30 };

    jouer(t, state);

    assert.ok(state.ball.vx < 0, `vx devait devenir négatif : ${state.ball.vx}`);
    assert.ok(state.ball.vy > 0, `vy devait rester positif : ${state.ball.vy}`);
  });

  test('flanc droit: la balle repart vers la droite', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 176, y: 110, r: BALL_R, vx: -300, vy: 30 };

    jouer(t, state);

    assert.ok(state.ball.vx > 0, `vx devait devenir positif : ${state.ball.vx}`);
    assert.ok(state.ball.vy > 0, `vy devait rester positif : ${state.ball.vy}`);
  });

  test('face haute: la balle repart vers le haut', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 96, r: BALL_R, vx: 30, vy: 300 };

    jouer(t, state);

    assert.ok(state.ball.vy < 0, `vy devait devenir négatif : ${state.ball.vy}`);
    assert.ok(state.ball.vx > 0, `vx devait rester positif : ${state.ball.vx}`);
  });

  test('face basse: la balle repart vers le bas', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 124, r: BALL_R, vx: 30, vy: -300 };

    jouer(t, state);

    assert.ok(state.ball.vy > 0, `vy devait devenir positif : ${state.ball.vy}`);
    assert.ok(state.ball.vx > 0, `vx devait rester positif : ${state.ball.vx}`);
  });
});

// Sur le coin, la balle arrive par la diagonale et pénètre autant sur les deux axes : les deux
// composantes doivent s'inverser. Une correction qui compare les deux pénétrations et n'en
// inverse qu'une passe les quatre faces et échoue ici.

describe('angle', () => {
  test('coin haut gauche: la balle repart en diagonale', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 96, y: 96, r: BALL_R, vx: 300, vy: 300 };

    jouer(t, state);

    assert.ok(state.ball.vx < 0, `vx devait devenir négatif : ${state.ball.vx}`);
    assert.ok(state.ball.vy < 0, `vy devait devenir négatif : ${state.ball.vy}`);
  });
});

// Le miroir géométrique de `brique` : mêmes quatre fixtures, mais on n'observe plus la vitesse,
// on observe la **position**.
//
// L'assertion est arithmétique et **pas** `!collides(ball, brick)` : `collides` fait partie du
// code sous test, et juger avec sa propre définition rendrait le cas plus facile pour une
// correction qui l'aurait assouplie. La tolérance couvre un calcul de pénétration en flottants
// qui atterrit à un ulp du bord.
const EPS = 1e-9;

describe('sortie', () => {
  test('flanc gauche: la balle ressort par la gauche', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 96, y: 110, r: BALL_R, vx: 300, vy: 30 };

    jouer(t, state);

    const bord = state.ball.x + BALL_R;
    assert.ok(bord <= 100 + EPS, `le bord droit de la balle devait revenir à x <= 100 : ${bord}`);
  });

  test('flanc droit: la balle ressort par la droite', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 176, y: 110, r: BALL_R, vx: -300, vy: 30 };

    jouer(t, state);

    const bord = state.ball.x - BALL_R;
    assert.ok(bord >= 172 - EPS, `le bord gauche de la balle devait revenir à x >= 172 : ${bord}`);
  });

  test('face haute: la balle ressort par le haut', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 96, r: BALL_R, vx: 30, vy: 300 };

    jouer(t, state);

    const bord = state.ball.y + BALL_R;
    assert.ok(bord <= 100 + EPS, `le bord bas de la balle devait revenir à y <= 100 : ${bord}`);
  });

  test('face basse: la balle ressort par le bas', (t) => {
    const state = createState(1);
    state.bricks = [{ x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 }];
    state.ball = { x: 136, y: 124, r: BALL_R, vx: 30, vy: -300 };

    jouer(t, state);

    const bord = state.ball.y - BALL_R;
    assert.ok(bord >= 120 - EPS, `le bord haut de la balle devait revenir à y >= 120 : ${bord}`);
  });
});

// Deux briques touchées dans la **même passe** de la boucle, qui parcourt toutes les briques
// vivantes. Le rebond doit s'appliquer une fois. Trois formes de correction se séparent ici :
// `vy = -vy` s'annule au second tour et la balle traverse ; `vy = Math.abs(vy)` est idempotente
// et passe ; une correction qui repositionne sort la balle du recouvrement avant d'atteindre la
// seconde brique et passe aussi.
//
// Chaque fixture est réglée pour que la face visée soit sans ambiguïté la **plus faible
// pénétration** - 1 px contre 3 sur l'axe de la couture - afin qu'un résolveur par pénétration
// minimale n'ait aucun choix à faire et que l'échec ne puisse venir que du double comptage.
//
// Les vitesses sont dix fois plus faibles qu'ailleurs, et c'est délibéré : une correction placée
// dans `step()`, qui intègre avant de résoudre, déplace la balle avant de la juger. À 60 px/s le
// déplacement est de 1 px et l'ordre des pénétrations tient quel que soit l'endroit où vit la
// correction.

describe('voisines', () => {
  test('couture horizontale: un seul rebond sur deux briques côte à côte', (t) => {
    const state = createState(1);
    state.bricks = [
      { x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 },
      { x: 100 + BRICK_W + BRICK_GAP, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 },
    ];
    // Centrée sur le gap (169..183 recouvre 3 px de chaque brique), et 1 px sous leur face
    // basse : l'axe vertical gagne pour les deux.
    state.ball = { x: 176, y: 126, r: BALL_R, vx: 6, vy: -60 };

    jouer(t, state);

    assert.ok(state.ball.vy > 0, `vy devait s'inverser une seule fois : ${state.ball.vy}`);
    assert.ok(state.ball.vx > 0, `vx devait rester positif : ${state.ball.vx}`);
  });

  test('couture verticale: un seul rebond sur deux briques superposées', (t) => {
    const state = createState(1);
    state.bricks = [
      { x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 },
      { x: 100, y: 100 + BRICK_H + BRICK_GAP, w: BRICK_W, h: BRICK_H, row: 1, alive: true, points: 10 },
    ];
    // Centrée sur le gap des rangées (117..131 recouvre 3 px de chaque brique), et 1 px dans
    // leur flanc gauche : l'axe horizontal gagne pour les deux.
    state.ball = { x: 94, y: 124, r: BALL_R, vx: 60, vy: 6 };

    jouer(t, state);

    assert.ok(state.ball.vx < 0, `vx devait s'inverser une seule fois : ${state.ball.vx}`);
    assert.ok(state.ball.vy > 0, `vy devait rester positif : ${state.ball.vy}`);
  });
});

// Le tunneling, avec les valeurs que le jeu produit lui-même et aucune autre. `ballSpeed(6)` vaut
// 710 px/s, et `DT_MAX` est le plafond que `boot()` applique à une frame qui a bégayé : 35.5 px de
// déplacement en un tour de boucle, contre 34 px à franchir (`BRICK_H` plus le diamètre de la
// balle). La détection échantillonne avant et après le saut, sans jamais voir le recouvrement du
// milieu.
//
// C'est le seul cas qui a besoin des trois étapes de `jouer()` : la balle est hors de la brique
// au départ, donc rien ne dévie avant le déplacement, et c'est le `frame()` d'après qui juge -
// l'ordre de `boot()`. Le `dt` passé en second argument est ce qui fait le saut.
//
// Pas de cas horizontal : franchir `BRICK_W` demanderait plus de 1720 px/s, un niveau que le jeu
// n'atteint pas. Un cas qu'aucune partie ne peut atteindre ne juge rien.

describe('traversee', () => {
  test('balle rapide: la brique n_est pas franchie sans être touchée', (t) => {
    const state = createState(6);
    const brique = { x: 100, y: 100, w: BRICK_W, h: BRICK_H, row: 0, alive: true, points: 10 };
    state.bricks = [brique];
    // Avant le déplacement la balle occupe y 121..135, sous la brique ; après, 85.5..99.5,
    // entièrement au-dessus. `vx` est nul : la dérive horizontale ne ferait que brouiller la
    // fixture, et ce cas ne juge que le franchissement vertical.
    state.ball = { x: 136, y: 128, r: BALL_R, vx: 0, vy: -ballSpeed(6) };

    jouer(t, state, DT_MAX);

    assert.ok(!brique.alive, 'la brique a survécu à une balle qui l_a traversée de part en part');
    assert.ok(state.ball.vy > 0, `la balle devait être renvoyée vers le bas : ${state.ball.vy}`);
  });
});

// Le seul chemin par lequel ces tests touchent le jeu : les quinze cas passent par ici et aucun
// n'appelle `frame()` ni `step()` lui-même. Trois étapes, dans cet ordre, et la première qui
// dévie la balle arrête la manœuvre.
//
// **`frame()` d'abord, et `step()` seulement si `frame()` n'a rien changé.** La collision des
// briques vit dans `frame()` aujourd'hui, mais l'extraire vers `step()` est une correction
// parfaitement valable : juger sur `frame()` seul noterait ce déplacement faux. Cette parade ne
// donne pas une seconde chance à une mauvaise réponse - une déviation sur le mauvais axe reste
// une déviation sur le mauvais axe - elle cherche ailleurs quand personne n'a répondu.
//
// **Puis `frame()` une seconde fois, si le déplacement n'a rien dévié non plus.** C'est l'ordre
// où `boot()` écrit sa boucle : `step()` déplace, `frame()` regarde ce que le déplacement a
// produit. C'est `traversee` qui en dépend - sa balle est hors de la brique au départ - et c'est
// aussi ce qui juge une correction qui ne se déclenche qu'après un déplacement au lieu de la
// déclarer fausse. Les onze premiers cas, dont la balle recouvre déjà la brique, ont dévié à la
// première étape ou ne dévieront pas : ce troisième tour ne leur change rien.
//
// L'arrêt à la première déviation est ce qui garde une correction présente aux deux endroits de
// compter deux fois. `bouge()` ne regarde que la vitesse : une brique éteinte ou une balle
// repositionnée ne comptent pas comme une déviation, et les cas qui les jugent lisent `state`
// eux-mêmes après le retour.
function jouer(t, state, dt = DT) {
  const { vx, vy } = state.ball;
  const bouge = () => state.ball.vx !== vx || state.ball.vy !== vy;

  frame(contexteFactice(), state);
  if (bouge()) return;

  step(state, dt);
  if (bouge()) {
    t.diagnostic('dévié par step() et non par frame()');
    return;
  }

  frame(contexteFactice(), state);
  if (bouge()) t.diagnostic('dévié par frame() après le déplacement de step()');
}

// Un contexte de canvas qui avale tout. `frame()` ne fait que des appels de dessin, donc rien
// n'a besoin de répondre juste : une fonction vide pour tout suffit.
function contexteFactice() {
  const rien = () => {};
  return new Proxy(
    {},
    {
      get: (_, nom) => (nom === 'canvas' ? { width: WIDTH, height: HEIGHT } : rien),
      set: () => true,
    },
  );
}
