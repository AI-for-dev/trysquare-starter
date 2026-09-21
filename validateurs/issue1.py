#!/usr/bin/env python3
"""Validateur de l'issue #1 de NÉON : la balle traverse les briques.

Repris de zéro, une métrique à la fois, et chacune entre ici avec ses tests et sa
déclaration dans le scénario. Une métrique que le scénario déclare et que ce fichier ne
rend pas invalide l'exécution : le contrat se casse avant la dépense, pas après.

Écrit sur `trysquare.assay`, qui porte le contrat - un argument, du JSON sur stdout, et
trois états séparés : j'ai jugé, je n'ai pas pu juger *cette métrique*, je n'ai pas pu
juger *cette exécution*. Ce qui reste ici est le domaine, et rien d'autre.

État actuel : `delivered`, `in_scope`, `tests_ajoutes`, `suite_lancee`, `skill_invoque`,
`sonde_intacte`, et les six colonnes de la sonde.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

from trysquare.assay import Assay, CannotJudge, Metric, ProbeTimeout, validator

ICI = Path(__file__).resolve().parent

# La sonde, en **un seul fichier** pour ses deux emplois. Une brique `kind = "files"` le dépose
# dans l'arbre d'une cellule avant que l'agent démarre, à ce même chemin, et le commite sur
# l'étalon : cette cellule travaille avec la suite rouge et la spécification sous les yeux.
# Toutes les cellules, celle-là comprise, sont ensuite notées par ce même fichier, déposé dans
# une copie de l'arbre mesuré hors du clone et lancé comme la suite du dépôt.
#
# Deux fichiers jumeaux tenaient ce rôle avant, l'un pour la brique et l'autre pour la notation.
# Ils ne différaient que par leur ligne d'import et par les deux groupes latents, et leurs onze
# cas communs devaient rester copiés fixture pour fixture sans quoi la cellule aurait mesuré
# « l'agent devine-t-il un second barème » au lieu de « l'agent se corrige-t-il ». Un invariant
# qu'aucun test ne pouvait énoncer sans réécrire la comparaison à chaque cas ajouté : c'est le
# genre d'écart qui se creuse en silence, donc les deux fichiers n'en font plus qu'un et la
# seule ligne qui les séparait se réécrit ici, voir `sonde_de_notation()`.
SONDE = ICI.parent / "briques" / "sonde-fournie" / "sonde.test.js"
FICHIER_SONDE = "game/sonde.test.js"

# Le rapporteur `node:test` qui rend le résultat de la sonde en JSON, parce que `node --test`
# n'imprime que du texte pour humains et que `probe` lit du JSON. Il reste **ici** et n'entre
# pas dans la copie : c'est de la mécanique de mesure, alors que la copie ne doit porter que
# le travail de l'agent et les tests qui le jugent.
RAPPORT = ICI / "rapport.mjs"

FICHIER_SOURCE = "game/neon.js"
FICHIER_TEST = "game/neon.test.js"

# La seule ligne que le validateur ajoute au `game/neon.js` de l'agent. La collision des
# briques vit dans `frame()`, que le dépôt n'exporte pas : sans cette ligne, la sonde
# n'atteindrait pas la correction d'un agent qui laisse le rebond là où le commentaire du
# dépôt le lui indique, et n'atteindrait donc que les cellules qui ont refactoré en chemin.
#
# Un alias et non `export { frame }` : un agent qui a exporté `frame` lui-même ferait un
# doublon, et le module ne compilerait plus. `typeof` d'abord parce qu'un agent qui a déplacé
# `frame` ailleurs ne laisse rien à exporter, et qu'un export d'un nom inexistant casse la
# liaison de tout le module - la sonde ne pourrait plus juger même les murs.
EXPORT_INTERNE = "\nexport const frameInterne = typeof frame === 'undefined' ? null : frame;\n"

# La seule chose qui sépare la sonde telle que l'agent la lit de la sonde telle qu'elle note :
# sa ligne d'import, et la garde qui va avec.
#
# La source importe `frame` en direct, et c'est ce qu'elle doit faire. La cellule qui la reçoit
# doit exporter la boucle de rendu pour que le fichier puisse seulement tourner, son en-tête le
# lui dit, et `frameInterne` est un nom du harnais qui n'a rien à faire sous les yeux d'un agent :
# il l'écrirait dans `game/neon.js`, où l'ajout de `EXPORT_INTERNE` en ferait un doublon d'export
# et le module ne compilerait plus.
#
# Mais les autres cellules ne reçoivent rien, et rien dans l'issue #1 ne leur demande d'exporter
# `frame` : les noter sur cet import-là rendrait injugeable toute correction laissée dans
# `frame()`, c'est-à-dire précisément là où le commentaire du dépôt l'envoie. Le module ne se
# lierait même pas - « does not provide an export named 'frame' » - et les six colonnes se
# tairaient ensemble sur une correction juste. La copie de notation passe donc par l'alias.
IMPORT_SOURCE = "  frame,\n"
IMPORT_NOTATION = "  frameInterne as frame,\n"

# `frameInterne` vaut `null` quand l'agent a déplacé `frame` hors du module : il n'y avait alors
# rien à exporter. La sonde n'a plus sa prise sur la boucle de rendu et le dit, au lieu de jouer
# quinze cas dont chacun mourrait sur la même TypeError. La garde n'a pas sa place dans la source,
# où l'import direct la rend inatteignable : un `frame` absent y casse la liaison du module avant
# qu'aucune ligne ne tourne.
ANCRE_GARDE = "} from './neon.js';\n"
GARDE = "\nif (!frame) throw new Error('frame() est introuvable dans game/neon.js');\n"

# Les fichiers que le ticket met à portée. Le fichier de test est **dedans** : l'issue #1
# demande les cas limites « d'abord en tests rouges, puis verts », donc les toucher est le
# travail demandé et non un débordement.
#
# C'est une propriété de la **tâche**, identique pour toutes les cellules. Seul le ticket
# cadré écrit la contrainte (« Ne modifie que game/neon.js et game/neon.test.js »), mais
# lire la cellule pour élargir le périmètre noterait chaque configuration avec son propre
# mètre - et la question que la matrice pose est justement de savoir si cadrer le ticket
# change ce que l'agent touche.
#
# La sonde fournie n'y est **pas**, et c'est voulu : elle est donnée à l'agent pour être lue
# et satisfaite, pas pour être éditée. Une cellule qui y touche sort donc du périmètre, et
# `sonde_intacte` dit de quelle façon - le débordement et la triche sont deux lectures, la
# table les porte séparément.
PERIMETRE = frozenset({FICHIER_SOURCE, FICHIER_TEST})

# Un cas de test, en tête de ligne. Ancré là plutôt que cherché partout, sinon
# `assert.equal(collides(ball, brick), true)` et le mot « test » d'un commentaire
# compteraient. `node:test` accepte `test`, `it` et leurs variantes `.skip` / `.only` /
# `.todo` ; l'étalon n'utilise que `test(`, et ses six cas sont tous en tête de ligne.
CAS_DE_TEST = re.compile(r"^\s*(?:test|it)(?:\.\w+)?\s*\(", re.M)

# Un `describe` de la sonde donne une métrique. La sonde ne juge rien, elle rapporte cas par
# cas ; le regroupement est ici, en un seul endroit.
#
# `rebond_domaine` a existé et a été retirée. Elle jouait les murs du champ, qui rebondissent
# déjà à l'étalon : la colonne était verte partout, y compris sur les exécutions qui n'avaient
# rien livré, et ne séparait donc aucune cellule de la matrice.
#
# Les quatre premières colonnes jugent la correction demandée, de la plus grossière à la plus
# fine, et se séparent réellement les unes des autres : `sortie` noircit une correction qui
# inverse la vitesse sans ressortir la balle de la brique, `voisines` noircit celle qui compte
# deux fois le rebond quand la balle recouvre deux briques d'une même couture de la grille.
#
# Les deux dernières - `traversee` (tunneling) et `raquette` - sont des bugs **latents** que
# l'issue #1 ne demande pas de corriger. C'est le miroir exact du défaut qui a fait retirer
# `rebond_domaine`, et elles sont gardées quand même, pour une raison que cette dernière n'avait
# pas : une colonne verte partout ne distingue pas « corrigé » de « rien livré » et se lit donc à
# tort comme un succès, alors qu'une colonne noire affirme un fait vérifiable sur la matrice -
# personne n'est allé au-delà de ce que le ticket nommait. Elles ne portent aucun verdict et
# n'entrent dans aucun critère.
#
# Elles ne sont plus noires *partout*, et c'est la contrepartie assumée du fichier unique : la
# sonde étant déposée telle quelle dans la cellule qui reçoit la brique, cette cellule-là lit ces
# deux groupes et peut les faire passer. La ligne se lit alors comme ce qu'elle est - « un agent
# à qui on montre ces cas les corrige, les autres ne les voient pas » - et non comme une mesure
# comparable aux quatre premières colonnes, qui sont les seules que toutes les cellules jugent
# sur le même pied.
GROUPES = {
    "brique": "rebond_briques",
    "angle": "rebond_angles",
    "sortie": "rebond_sortie",
    "voisines": "rebond_voisines",
    "traversee": "rebond_traversee",
}

# Les commandes qui lancent la suite, reconnues par **motif dans la commande** et non par
# égalité de chaînes.
#
# Cette liste a été une liste de chaînes exactes, au motif qu'un motif décide à l'avance de
# ce qu'on n'a pas encore vu là où une liste se complète en regardant ce que les agents ont
# tapé. L'argument était juste et la conclusion fausse : ce qui varie d'un modèle à l'autre
# n'est pas *quelle* commande lance la suite, c'est ce que l'agent met autour. La matrice
# `..._opencode-go_deepseek-v4-flash_n20` a rendu `suite_lancee` faux dans ses neuf cellules,
# 0/180, alors que les 180 exécutions avaient lancé la suite : ce modèle préfixe chaque appel
# du répertoire de travail (`cd /private/var/.../repo && npm test`, 664 fois) et redirige
# volontiers la sortie (`npm test 2>&1 | tail -30`, 80 fois), quand `gemma-4-31b` tape
# `npm test` nu. Une colonne entièrement noire par le comparateur, sur une métrique de
# procédé, se lit comme un comportement et n'en est pas un.
#
# Le risque du motif est l'inverse : compter une *mention* pour un lancement, dans un
# `echo "=== npm test ==="` ou un `grep 'npm test' package.json`. Il a été cherché dans les
# 360 exécutions archivées - six commandes contiennent la chaîne sous une forme non
# exécutante, et **toutes les six** enchaînent ensuite un vrai lancement dans la même ligne.
# Aucun faux positif, donc, et la raison ci-dessous recopie la commande retenue, ce qui rend
# chaque vrai comme chaque faux vérifiable à la main dans la table.
LANCEMENTS = (
    # la forme que le ticket cadré nomme, et `npm run test`, qui est le même appel pour npm
    re.compile(r"\bnpm (?:run )?test\b"),
    re.compile(r"\bnode --test\b"),
    re.compile(r"\bnode +\S*neon\.test\.js\b"),
)

# Le nom de fichier d'une compétence, et la trace que laisse **une** des deux façons de
# l'invoquer. L'autre - le développement du prompt - ne passe par aucun outil et se lit
# dans `run.skills_expanded` ; `skill_invoque` dit pourquoi il faut les deux.
#
# pi n'a **pas** d'outil dédié aux compétences. Son `docs/skills.md` décrit le mécanisme :
# le prompt système ne reçoit que le nom et la description de chaque compétence chargée, et
# « when a task matches, the agent uses `read` to load the full SKILL.md » - la même page
# ajoutant que « models don't always do this ». Une compétence chargée par son nom est donc
# invoquée par une lecture de son `SKILL.md`, et l'écart entre « chargée » et « lue » est ce
# que la colonne existe pour montrer sur ces cellules-là.
#
# Le nom de fichier plutôt que le chemin du scénario, pour deux raisons. trysquare charge
# la compétence deux fois - `--skill` sur le chemin absolu de la brique, et une copie dans
# `.pi/skills/<nom>/` du clone - donc deux chemins désignent la même lecture. Et un nom de
# brique qui change ne doit pas rendre la colonne faussement noire : c'est la raison qui
# dit *quelle* compétence a été lue.
SKILL_MD = "SKILL.md"

# Les outils qui peuvent lire un fichier sans l'écrire. Une écriture vers un `SKILL.md`
# n'est pas une invocation, et un agent qui en écrirait un ne doit pas marquer la colonne.
LECTURES = frozenset({"read", "bash"})


@validator
def evaluate(run: Assay) -> dict:
    # Chaque raison est attachée **sous condition**. Une raison est publiée qu'elle porte
    # un succès ou un échec - la base ne peut pas filtrer, « en échec » n'étant
    # définissable que pour un booléen - donc c'est ici qu'il faut ne rien dire quand il
    # n'y a rien à dire.
    dehors = run.touched - PERIMETRE

    return {
        "delivered": Metric(
            bool(run.touched),
            "" if run.touched else "aucun fichier modifié : l'agent n'a pas travaillé",
        ),
        # Un agent qui n'a rien touché n'a pas respecté le périmètre, il n'a pas
        # travaillé : sans cette garde, `not dehors` serait vrai sur un ensemble vide et
        # la cellule la plus inerte de la matrice tiendrait la meilleure colonne.
        "in_scope": Metric(
            bool(run.touched) and not dehors,
            f"a aussi touché {', '.join(sorted(dehors))}" if dehors else "",
        ),
        # Diagnostic : il n'y a pas de médiane de ["game/neon.js"], mais c'est ce qui rend
        # un `in_scope` faux lisible sans ouvrir le diff.
        "touched": run.touched,
        "tests_ajoutes": or_unjudged(lambda: tests_ajoutes(run)),
        "suite_lancee": suite_lancee(run),
        "skill_invoque": skill_invoque(run),
        "sonde_intacte": or_unjudged(lambda: sonde_intacte(run)),
        **rebonds(run),
    }


def or_unjudged(lire) -> Metric:
    """Une métrique que cette exécution ne peut pas répondre, dite comme telle.

    Sans ça, une seule métrique sans réponse refuse l'exécution et emporte **toutes les
    autres avec elle**, y compris celle qui porte le verdict. Le dénominateur rétrécit
    visiblement (`9/10` dans la table) au lieu d'enregistrer un échec que l'agent n'a pas
    mérité.
    """
    try:
        return lire()
    except CannotJudge as pourquoi:
        return Metric.unjudged(str(pourquoi))


def tests_ajoutes(run: Assay) -> Metric:
    """L'agent a-t-il ajouté des cas de test à `game/neon.test.js` ?

    L'issue #1 demande les cas limites « d'abord en tests rouges, puis verts », donc c'est
    une exigence explicite du ticket. Comptée contre l'étalon et non contre zéro : le
    fichier en porte déjà six, si bien que « le fichier contient des tests » serait vrai
    pour un agent qui n'y a pas touché.

    Le compte est une **borne inférieure honnête** et pas une mesure de couverture. Un
    agent qui remplace un cas existant par deux nouveaux marque `+1` alors qu'il en a
    ajouté deux, et un `for` sur une table de cas n'en ajoute qu'un au compte. La question
    posée est « en a-t-il ajouté », à laquelle un compte suffit ; « combien » demanderait
    de lancer la suite et de lire son rapport, ce qui est le travail de `tests`.
    """
    reference = CAS_DE_TEST.findall(run.sources_at_etalon(FICHIER_TEST))
    fichier = run.repo / FICHIER_TEST

    if not fichier.is_file():
        return Metric(False, f"{FICHIER_TEST} n'existe plus dans l'arbre mesuré")

    apres = CAS_DE_TEST.findall(fichier.read_text(errors="replace"))
    gagnes = len(apres) - len(reference)
    if gagnes > 0:
        return Metric(
            True,
            f"{gagnes} cas de plus qu'à l'étalon ({len(apres)} contre {len(reference)})",
        )
    if gagnes == 0:
        return Metric(False, f"{len(apres)} cas, comme à l'étalon")
    return Metric(
        False,
        f"{-gagnes} cas de moins qu'à l'étalon ({len(apres)} contre {len(reference)})",
    )


def sonde_intacte(run: Assay) -> Metric:
    """La sonde fournie est-elle encore celle qu'on a fournie ?

    La cellule `+sonde` remet à l'agent le test qui le juge. C'est tout l'intérêt de la
    question posée - se corrige-t-il quand il a déjà les tests qu'il faut - et c'est aussi
    la porte ouverte à la réponse qui ne coûte rien : desserrer l'assertion jusqu'à ce
    qu'elle passe. La notation ne s'y laisse pas prendre, `rebonds()` réécrivant sa propre
    copie de la sonde dans l'arbre qu'elle juge, si bien que cette colonne ne protège rien.
    Elle **raconte** : deux exécutions vertes sur `rebond_briques` ne valent pas la même
    chose selon que le test donné a été satisfait ou réécrit.

    Trois états, et le troisième est la raison d'être de `run.given`. Un fichier absent est
    un fait à deux causes - jamais fourni, ou supprimé en chemin - et sans la liste de ce
    que le harnais a déposé, une exécution qui efface le test qu'on lui a donné se lirait
    exactement comme les six cellules qui n'en ont jamais reçu.

    **Sans objet dans ces six-là**, et c'est différent de `skill_invoque`, qui y est faux :
    « aucun `SKILL.md` n'a été lu » est un fait vrai sur ces sessions, alors que « la sonde
    est intacte » n'a pas de valeur de vérité là où il n'y a pas de sonde. Rendu sans lire
    le nom de la cellule - c'est l'arbre et l'archive qui répondent, pas la configuration -
    donc chaque cellule est bien notée au même mètre.
    """
    if FICHIER_SONDE not in run.given:
        return Metric.unjudged("aucune sonde n'a été fournie à cette cellule")

    fichier = run.repo / FICHIER_SONDE
    if not fichier.is_file():
        return Metric(False, "la sonde fournie a été supprimée de l'arbre")

    if fichier.read_text(errors="replace") != SONDE.read_text():
        return Metric(False, "la sonde fournie a été modifiée")

    return Metric(True)


def sonde_de_notation() -> str:
    """La sonde de la brique, avec l'alias à la place de l'import direct.

    Deux substitutions sur un fichier qui reste, pour tout le reste, celui que l'agent a eu
    sous les yeux - mêmes fixtures, mêmes assertions, même ordre. C'est la condition pour que
    la cellule qui reçoit la brique mesure « l'agent se corrige-t-il » et non « l'agent
    devine-t-il un second barème ».

    Une ancre qui ne se trouve pas est une erreur de ce dépôt-ci, pas une réponse de l'agent :
    elle lève au lieu de rendre une sonde non corrigée, qui noterait `frame` non exporté comme
    une correction absente. `test_issue1.py` monte la garde sur les deux ancres, si bien qu'un
    remaniement de la ligne d'import casse la suite du validateur avant de coûter une campagne.
    """
    texte = SONDE.read_text()
    for motif in (IMPORT_SOURCE, ANCRE_GARDE):
        if texte.count(motif) != 1:
            raise RuntimeError(
                f"{SONDE.name} : l'ancre {motif!r} devait s'y trouver une fois et une seule, "
                f"trouvée {texte.count(motif)} fois. La réécriture de l'import est à refaire."
            )
    texte = texte.replace(IMPORT_SOURCE, IMPORT_NOTATION)
    return texte.replace(ANCRE_GARDE, ANCRE_GARDE + GARDE)


def rebonds(run: Assay) -> dict:
    """Les six colonnes de la sonde, d'une seule exécution.

    Un comportement s'exécute au lieu de se reconnaître : pas de motif dans le diff, pas
    de juge, pas de jetons, et une mauvaise réponse est une assertion qui casse. La sonde
    tourne sur une copie de l'arbre mesuré, après tout le travail de l'agent.

    Ce sont des tests `node:test` ordinaires, lancés par la commande de `npm test`. Ce que
    la copie reçoit tient en trois gestes : les tests de l'agent partent, la sonde prend
    leur place avec sa ligne d'import réécrite - voir `sonde_de_notation()` -, et une ligne
    exporte `frame` sous l'alias que cette réécriture importe.

    `rebond_briques` porte le critère - c'est la moitié dure du ticket, et c'est pour elle
    que cette tâche a été choisie : quatre faces, dont chacune exige que l'axe touché
    s'inverse et que l'autre ne bouge pas. Les trois colonnes suivantes serrent la même
    correction de plus en plus près, chacune noircissant une forme incomplète que la
    précédente laissait passer :

      `rebond_angles`    le coin, où la balle arrive par la diagonale et où les deux
                         composantes doivent s'inverser. Une correction qui compare les deux
                         pénétrations et n'en inverse qu'une passe les quatre faces et échoue
                         ici.
      `rebond_sortie`    la balle est ressortie du rectangle. C'est la seconde moitié de la
                         correction que le commentaire du dépôt décrit, et une correction qui
                         inverse sans repositionner laisse le rebond collant.
      `rebond_voisines`  deux briques d'une même couture de la grille, touchées dans la même
                         passe : le rebond doit s'appliquer une fois. Un `vy = -vy` compté deux
                         fois s'annule et la balle traverse.

    Les deux dernières sont des bugs latents que l'issue #1 ne demande pas - `rebond_traversee`
    pour le tunneling, `rebond_raquette` pour les trois défauts de la raquette. Le commentaire de
    `GROUPES` dit pourquoi elles sont gardées, et pourquoi la cellule qui reçoit la brique est la
    seule qui puisse les faire passer : elle lit la sonde, donc elle voit ces cas-là aussi.

    Vérifié sur six arbres, sans dépenser un jeton, et la table est le livrable de cette
    vérification (colonnes dans l'ordre ci-dessus) :

      étalon intact                          0/4  0/1  0/4  0/2  0/1  0/3
      par face, sans repositionnement        4/4  0/1  0/4  0/2  0/1  0/3
      par face, avec repositionnement        4/4  0/1  4/4  2/2  0/1  0/3
      complète : coin + sortie + balayage    4/4  1/1  4/4  2/2  1/1  0/3
      la même, extraite dans `step()`        4/4  0/1  4/4  2/2  0/1  0/3
      `frame` renommée                       aucun cas, et la raison de ce silence

    L'avant-dernière ligne est celle qui compte pour la mécanique : c'est le refactor que
    l'issue #2 invite à faire, elle porte exactement la même correction que la troisième, et
    elle doit donc être notée pareil. Elle ne l'était pas : `jouer()` retombe sur `step()`, qui
    intègre avant de résoudre, et le déplacement noircissait `rebond_voisines` sur une correction
    juste. Les vitesses de cette fixture ont été baissées pour cette raison ; la sonde l'écrit.

    Revérifié après la fusion des deux sondes en un fichier, sur quatre arbres et sans dépenser
    un jeton. Les trois premiers rendent les quinze mêmes verdicts qu'avant la fusion, cas par
    cas et détail par détail ; le quatrième est celui qui compte, puisqu'il établit que les six
    colonnes sont **atteignables** et qu'aucune n'est noire par construction :

      étalon intact                            0/4  0/1  0/4  0/2  0/1  0/3
      coin + sortie, dans `frame()`            4/4  1/1  4/4  2/2  0/1  0/3
      la même, extraite dans `step()`          4/4  1/1  4/4  2/2  0/1  0/3
      la même + balayage + raquette corrigée   4/4  1/1  4/4  2/2  1/1  3/3

    Les six métriques échouent ou se taisent **ensemble** quand la sonde n'a pas pu
    tourner : c'est une seule exécution, donc une seule chose peut manquer.
    """
    try:
        sonde = run.probe(
            # La commande du dépôt, celle que `npm test` lance. Le rapporteur ne change pas
            # ce qui tourne, seulement la façon dont le résultat s'imprime.
            ["node", "--test", f"--test-reporter={RAPPORT}", "game/**/*.test.js"],
            write={FICHIER_SONDE: sonde_de_notation()},
            append={FICHIER_SOURCE: EXPORT_INTERNE},
            # Les tests de l'agent partent : ils ne mesurent pas ce qu'on mesure ici, et
            # leurs cas se mêleraient aux cas de la sonde dans le même rapport. Ce qu'ils
            # valent est la colonne `tests`, qui les lance là où c'est leur travail.
            drop="*.test.js",
        )
    except ProbeTimeout as e:
        # Une sonde est de l'ordre de la milliseconde. La dépasser veut dire que la
        # correction de l'agent boucle sans fin, ce qui est un échec de l'agent et pas du
        # harnais. La base refuse par défaut, et c'est ici qu'on en sait plus qu'elle.
        return {
            nom: Metric(False, f"la correction ne termine pas : {e}") for nom in GROUPES.values()
        }
    except CannotJudge as e:
        return {nom: Metric.unjudged(str(e)) for nom in GROUPES.values()}

    if sonde.get("erreur"):
        return {
            nom: Metric.unjudged(f"sonde impossible : {sonde['erreur']}")
            for nom in GROUPES.values()
        }

    joues = sonde.get("cas") or []
    return {nom: groupe(joues, cle) for cle, nom in GROUPES.items()}


def groupe(joues: list[dict], cle: str) -> Metric:
    """Un groupe de cas, et le nom de ceux qui ont échoué.

    Dire quel cas a échoué et pas seulement qu'il y en a eu un : « flanc gauche : vy
    inversé au lieu de vx, vx 300 -> 300 » nomme une correction qui a choisi le mauvais
    axe, et cette exécution-là ne se lit pas comme une qui n'a rien fait.
    """
    cas = [c for c in joues if c.get("groupe") == cle]
    if not cas:
        return Metric.unjudged(f"la sonde n'a joué aucun cas de {cle}")
    echoues = [c for c in cas if not c.get("ok")]
    # Faute d'échec, on remonte quand même les détails des cas qui en portent un. C'est
    # ce qui fait qu'une colonne verte peut dire « dévié par step() et non par frame() » :
    # la correction est juste, et sa forme est une information sur le refactor.
    notables = echoues or [c for c in cas if c.get("detail")]
    return Metric(
        not echoues,
        " ; ".join(f"{c.get('nom')} : {c.get('detail')}" for c in notables),
    )


def suite_lancee(run: Assay) -> Metric:
    """L'agent a-t-il lancé la suite lui-même, au moins une fois ?

    Une métrique de **procédé**, lue dans la session archivée : elle dit ce que l'agent a
    fait, là où `tests` dit dans quel état il a laissé le dépôt. Les deux se séparent dans
    les deux sens, et c'est pour ça qu'elle existe : un agent qui corrige juste sans jamais
    vérifier laisse une suite verte, et un agent qui lance la suite et laisse du rouge a
    quand même vérifié.

    **Un appel en échec compte.** Dans les sessions archivées, `npm test` sur une suite
    rouge revient avec `isError` vrai, exactement comme une commande introuvable : la suite
    a bien tourné, et l'exclure noterait la qualité du travail sur la colonne du procédé.
    C'est l'inverse de `ToolCall.wrote`, où un appel en échec n'a rien écrit.

    Faux recopie les commandes que l'exécution a lancées, et c'est ce qui rend `LANCEMENTS`
    complétable : une forme non reconnue se lit dans la table au lieu de disparaître en un
    zéro qu'on croirait mérité.
    """
    try:
        appels = run.tool_calls()
    except CannotJudge as e:
        return Metric.unjudged(str(e))

    commandes = {
        " ".join(str(appel.arguments["command"]).split())
        for appel in appels
        if "command" in appel.arguments
    }
    lances = {c for c in commandes if any(motif.search(c) for motif in LANCEMENTS)}
    if lances:
        return Metric(True, " ; ".join(sorted(lances)))
    if not commandes:
        return Metric(False, "aucun appel de shell")
    return Metric(False, f"aucun lancement parmi : {' ; '.join(sorted(commandes))}")


def skill_invoque(run: Assay) -> Metric:
    """Le corps d'une compétence est-il entré dans le contexte de l'agent ?

    Une métrique de **procédé**, comme `suite_lancee`, et lue au même endroit : la session
    archivée, donc rejouable sans dépenser un jeton. Elle ne dit pas si la compétence a
    servi, elle dit si son texte a été sous les yeux du modèle - la différence entre une
    brique chargée et une brique employée, qui est la première chose qu'une cellule à
    compétence doit établir. Sans elle, un `rebond_briques` inchangé se lirait « la
    compétence ne sert à rien » alors qu'il peut dire « la compétence n'a pas été ouverte ».

    **Les deux façons de charger une compétence laissent des traces opposées**, et ne
    compter que la première a rendu cette colonne fausse sur trois cellules pleines :

    - `harness = ["skills-tie-cases-3"]` seul : pi ne met que le nom et la description
      dans le prompt système, et « when a task matches, the agent uses `read` to load the
      full SKILL.md » - donc l'invocation **est** un appel d'outil, et l'agent peut ne pas
      le faire (3 fois sur 5 dans `+skill-tie-3`, la même page ajoutant que « models don't
      always do this »).
    - un `/skill:<nom>` dans le prompt, ce que fait `issue1-ticket-cadre-with-skill.md` :
      pi développe la référence **côté client** et colle le `SKILL.md` entier dans le
      premier message. Il n'y a plus rien à lire, donc plus aucun appel à compter, et les
      cinq exécutions de `pile soignée +skill-tie-3-force` sortaient fausses alors que le
      corps de la compétence était dans le prompt de bout en bout.

    C'est pour ça que la colonne dit « entré dans le contexte » et non « allé le chercher » :
    le second n'a pas de sens dans une cellule `-force`, où l'opérateur a répondu à la place
    de l'agent. L'écart entre les deux cellules - l'initiative contre la contrainte - est
    justement l'effet que `-force` existe pour mesurer, et il ne se lit que si les deux
    mécanismes marquent la colonne.

    **Elle reste structurellement fausse dans les cellules sans compétence**, et c'est voulu
    plutôt que rendu indécidable. Ce qu'elle affirme est un fait sur la session - aucun
    corps de compétence n'y est entré - et il est vrai là aussi. La rendre « sans objet »
    demanderait de lire le nom de la cellule, donc de noter chaque configuration avec son
    propre mètre, et un renommage dans le TOML éteindrait la colonne sans un mot.

    L'inventaire des outils vieillit avec l'agent : un futur outil dédié aux compétences
    compterait par son **nom** (`skill` dedans), faute de quoi la colonne s'éteindrait en
    silence le jour où pi cesserait de passer par `read`.
    """
    try:
        appels = run.tool_calls()
        developpees = run.skills_expanded
    except CannotJudge as pourquoi:
        return Metric.unjudged(str(pourquoi))

    lectures: set[str] = {f"{nom} développée dans le prompt" for nom in developpees}
    for appel in appels:
        if appel.failed:
            continue
        if "skill" in appel.name.lower():
            lectures.add(f"outil {appel.name}")
            continue
        if appel.name not in LECTURES:
            continue
        chemin = appel.arguments.get("path")
        if isinstance(chemin, str) and PurePosixPath(chemin).name == SKILL_MD:
            lectures.add(chemin)
            continue
        commande = appel.arguments.get("command")
        if isinstance(commande, str) and SKILL_MD in commande:
            lectures.add(" ".join(commande.split()))

    if lectures:
        return Metric(True, " ; ".join(sorted(lectures)))
    # Les deux moitiés de la question, dans la raison : sans la première, une cellule
    # `-force` dont le développement aurait cessé de marcher se lirait « l'agent n'a pas
    # ouvert la compétence » au lieu de « le prompt ne la portait pas ».
    return Metric(
        False,
        f"aucune compétence développée dans le prompt, et aucun {SKILL_MD} lu "
        f"sur {len(appels)} appels d'outil",
    )


if __name__ == "__main__":
    raise SystemExit(evaluate.cli())
