#!/usr/bin/env python3
"""Tests du validateur de l'issue #1, reprise en cours comme le validateur lui-même.

Ce qui est couvert ici : `skill_invoque` et `sonde_intacte`, entrées avec ces tests, et le
**contrat des métriques** - chaque nom déclaré par un scénario est bien rendu, vérifié en
appelant le validateur plutôt qu'en relisant son texte. C'est le seul oubli du lot qui ne se
découvre qu'après avoir dépensé une matrice.

S'y ajoute un test sur le **matériau** : la sonde est un seul fichier pour ses deux emplois,
et `sonde_de_notation()` n'en réécrit que la ligne d'import. Les deux ancres de cette réécriture
sont gardées ici, parce qu'une ancre qui ne mord plus rend une sonde non corrigée - `frame` non
exporté se lirait alors comme une correction absente, sur toute une campagne.

Ce qui ne l'est pas encore : la sonde et ses fixtures, `tests_ajoutes`, `in_scope`. Ils
étaient couverts dans `../../trysquare-campaign-old/validateurs/test_issue1.py`, contre
des arbres réels, et leur reprise attend celle des fixtures.

    cd validateurs
    uv run --no-project --with ../../../../trysquare python -m unittest test_issue1 -v
"""

from __future__ import annotations

import re
import tempfile
import tomllib
import unittest
from pathlib import Path

import issue1
from trysquare.assay import Assay, Metric, ToolCall, report

ICI = Path(__file__).resolve().parent
SCENARIOS = ICI.parent / "scenarios"

# Le chemin absolu de la brique, tel que `--skill` le passe : c'est sous cette forme que
# l'agent voit la compétence, et donc sous cette forme qu'il la lit.
BRIQUE = "/tmp/campaign/briques/skills/test-gaps/SKILL.md"
# La copie que trysquare dépose dans le clone. Le même fichier, un autre chemin, et la
# raison pour laquelle la détection porte sur le nom de fichier et non sur le chemin.
COPIE = ".pi/skills/test-gaps/SKILL.md"


def lecture(chemin: str, **reste) -> ToolCall:
    return ToolCall(name="read", arguments={"path": chemin, **reste}, failed=False)


def shell(commande: str, failed: bool = False) -> ToolCall:
    return ToolCall(name="bash", arguments={"command": commande}, failed=failed)


class TestSuiteLancee(unittest.TestCase):
    """La colonne dit « l'agent a lancé la suite lui-même », et elle l'a dit faux 180 fois
    de suite sur une matrice où les 180 exécutions l'avaient lancée.

    La cause était un comparateur : `LANCEMENTS` était une liste de chaînes exactes, et
    `deepseek-v4-flash` préfixe chaque appel du répertoire de travail là où `gemma-4-31b`
    tape `npm test` nu. Ce qui varie d'un modèle à l'autre n'est pas la commande, c'est ce
    que l'agent met autour, donc la reconnaissance est un motif dans la commande.

    Les formes ci-dessous sont **relevées dans les archives** de `results/`, pas imaginées :
    c'est ce qui les rend utiles quand un troisième modèle en apportera une quatrième.
    """

    def lance(self, *commandes: str) -> Metric:
        return issue1.suite_lancee(
            Assay.fake(tool_calls=tuple(shell(c) for c in commandes))
        )

    def test_la_forme_nue_compte(self):
        """`gemma-4-31b`, 133 fois dans les archives."""
        self.assertTrue(self.lance("npm test"))

    def test_la_forme_prefixee_du_repertoire_compte(self):
        """`deepseek-v4-flash`, 664 fois : la forme que le comparateur exact refusait."""
        self.assertTrue(self.lance("cd /tmp/campaign/ab12/repo && npm test"))

    def test_la_forme_a_sortie_redirigee_compte(self):
        """80 fois dans les archives, et refusée elle aussi."""
        self.assertTrue(self.lance("npm test 2>&1 | tail -30"))

    def test_npm_run_test_compte(self):
        self.assertTrue(self.lance("npm run test"))

    def test_node_test_compte_quel_que_soit_le_chemin(self):
        self.assertTrue(self.lance("node --test game/neon.test.js"))
        self.assertTrue(self.lance("cd /tmp/x && node --test"))
        self.assertTrue(self.lance("node game/neon.test.js"))

    def test_un_lancement_en_echec_compte_quand_meme(self):
        """Une suite rouge revient avec `isError`, comme une commande introuvable. La suite
        a bien tourné, et l'exclure noterait la qualité du travail sur la colonne du procédé.
        """
        metrique = issue1.suite_lancee(
            Assay.fake(tool_calls=(shell("npm test", failed=True),))
        )
        self.assertTrue(metrique)

    def test_un_echo_qui_annonce_le_lancement_ne_suffit_pas_seul(self):
        """Le risque propre au motif, et sa borne. Les six commandes des archives qui
        mentionnent la chaîne sans l'exécuter enchaînent toutes un vrai lancement dans la
        même ligne, donc aucun faux positif n'y est observable ; ce cas garde la seule forme
        où la distinction serait visible.
        """
        self.assertFalse(self.lance('echo "il faudrait lancer npm-test"'))

    def test_sans_lancement_la_raison_recopie_les_commandes(self):
        """C'est cette raison qui a rendu le défaut visible : elle montrait un `npm test`
        dans la liste des commandes « où aucun lancement n'a été trouvé ».
        """
        metrique = self.lance("ls -la", "cat package.json")
        self.assertFalse(metrique)
        self.assertIn("ls -la", metrique.reason)
        self.assertIn("cat package.json", metrique.reason)

    def test_sans_aucun_appel_de_shell_la_raison_le_dit(self):
        metrique = issue1.suite_lancee(Assay.fake(tool_calls=(lecture("game/neon.js"),)))
        self.assertFalse(metrique)
        self.assertIn("aucun appel de shell", metrique.reason)


class TestSkillInvoque(unittest.TestCase):
    """La colonne dit « le corps de la compétence est entré dans le contexte », pas « la
    compétence a servi ». Elle sépare une brique chargée d'une brique lue.

    Et elle compte les **deux** mécanismes par lesquels ce corps arrive, parce qu'ils
    laissent des traces opposées : chargée par son nom, l'agent doit lire le `SKILL.md`
    lui-même, ce qui est un appel d'outil ; référencée par `/skill:<nom>` dans le prompt,
    elle est développée côté client et il n'y a plus rien à lire. Ne compter que le premier
    a rendu les cinq exécutions de `pile soignée +skill-tie-3-force` fausses alors que le
    corps était dans leur prompt de bout en bout.
    """

    def invoque(self, *appels: ToolCall, developpees: tuple[str, ...] = ()) -> Metric:
        return issue1.skill_invoque(
            Assay.fake(tool_calls=tuple(appels), skills_expanded=developpees)
        )

    def test_lire_la_brique_compte(self):
        self.assertTrue(self.invoque(lecture(BRIQUE)))

    def test_une_competence_developpee_dans_le_prompt_compte_sans_aucun_appel(self):
        """Le cas `-force`, et celui qui manquait. `/skill:tie-cases-3` fait coller le
        `SKILL.md` entier dans le premier message : le corps est là avant que l'agent bouge,
        donc il n'a aucune raison de le lire et n'en lit aucun. La raison nomme la
        compétence, sinon la colonne verte ne dirait pas laquelle."""
        metrique = self.invoque(shell("npm test"), developpees=("tie-cases-3",))
        self.assertTrue(metrique)
        self.assertIn("tie-cases-3", metrique.reason)

    def test_developpee_et_relue_ne_compte_quune_fois_par_trace(self):
        """Les deux mécanismes peuvent coexister - rien n'interdit à un agent de relire une
        compétence qu'on lui a déjà collée - et la raison doit alors dire les deux, parce que
        ce ne sont pas les mêmes faits sur la session."""
        metrique = self.invoque(lecture(BRIQUE), developpees=("test-gaps",))
        self.assertTrue(metrique)
        self.assertIn("test-gaps", metrique.reason)
        self.assertIn(BRIQUE, metrique.reason)

    def test_lire_la_copie_du_clone_compte_aussi(self):
        """Les deux chemins désignent la même compétence : trysquare la charge par
        `--skill` **et** la copie dans `.pi/skills/`, et l'agent peut lire l'un ou l'autre.
        Une détection par chemin exact en manquerait la moitié."""
        self.assertTrue(self.invoque(lecture(COPIE)))

    def test_un_cat_dans_le_shell_compte(self):
        self.assertTrue(self.invoque(shell(f"cat {COPIE}")))

    def test_sans_lecture_cest_faux_et_la_raison_dit_les_deux_moities(self):
        """Le cas des cellules sans compétence, et celui d'une cellule qui en a une et ne
        l'ouvre pas. Les deux rendent faux, et c'est ce que le scénario assume : la raison
        est un fait sur la session, vrai dans les deux cas.

        Elle nomme les **deux** moitiés de la question, sinon une cellule `-force` dont le
        développement aurait cessé de marcher se lirait « l'agent n'a pas ouvert la
        compétence » au lieu de « le prompt ne la portait pas »."""
        metrique = self.invoque(lecture("game/neon.js"), shell("npm test"))
        self.assertFalse(metrique)
        self.assertIn("2 appels", metrique.reason)
        self.assertIn("développée dans le prompt", metrique.reason)

    def test_une_execution_sans_aucun_appel_est_fausse_et_le_dit(self):
        metrique = self.invoque()
        self.assertFalse(metrique)
        self.assertIn("0 appels", metrique.reason)

    def test_ecrire_un_skill_md_nest_pas_lin_invoquer(self):
        """Une écriture n'est pas une lecture. Un agent qui écrirait un `SKILL.md` - par
        zèle ou par erreur - ne doit pas marquer une colonne de procédé."""
        ecriture = ToolCall(name="write", arguments={"path": COPIE}, failed=False)
        self.assertFalse(self.invoque(ecriture))

    def test_un_appel_en_echec_ne_compte_pas(self):
        """Contrairement à `suite_lancee`, où un `npm test` qui revient rouge a bien lancé
        la suite. Ici l'appel en échec n'a rien rendu : le corps de la compétence n'est pas
        entré dans le contexte, donc elle n'a pas été invoquée."""
        self.assertFalse(self.invoque(shell(f"cat {COPIE}", failed=True)))

    def test_un_outil_dedie_compterait_par_son_nom(self):
        """L'inventaire des outils vieillit avec l'agent. pi passe aujourd'hui par `read`
        (`docs/skills.md`) ; le jour où il gagne un outil dédié, la colonne doit continuer
        de compter au lieu de s'éteindre en silence."""
        futur = ToolCall(name="skill", arguments={"name": "test-gaps"}, failed=False)
        self.assertTrue(self.invoque(futur))

    def test_sans_session_la_metrique_se_tait_au_lieu_de_dire_faux(self):
        """Une session absente vient du harnais et ne dit rien de l'agent. `unjudged`
        rétrécit le dénominateur visiblement, là où faux enregistrerait un manquement que
        l'agent n'a pas commis."""
        metrique = issue1.skill_invoque(Assay.fake())
        self.assertIsNone(report({"skill_invoque": metrique})["metrics"].get("skill_invoque"))

    def test_une_base_sans_developpement_se_tait_au_lieu_de_ne_compter_quune_moitie(self):
        """Une base antérieure à `skills_expanded` ne peut répondre qu'à la moitié de la
        question, et une moitié de réponse est exactement le défaut qu'on vient de corriger :
        toutes les cellules `-force` sortiraient fausses. Se taire rétrécit le dénominateur
        visiblement au lieu de publier une colonne dont la lecture est fausse."""
        metrique = issue1.skill_invoque(Assay.fake(tool_calls=(lecture("game/neon.js"),)))
        self.assertIsNone(report({"skill_invoque": metrique})["metrics"].get("skill_invoque"))


class TestSondeIntacte(unittest.TestCase):
    """Le test qu'on a donné à l'agent est-il encore celui qu'on a donné ?

    La cellule `+sonde` remet à l'agent le test qui le juge, ce qui ouvre la réponse qui ne
    coûte rien : desserrer l'assertion. La notation ne s'y laisse pas prendre - elle réécrit
    sa propre copie - donc cette colonne ne protège rien, elle sépare deux exécutions vertes
    qui n'ont pas fait la même chose.
    """

    def arbre(self, tmp: str, contenu: str | None) -> Path:
        racine = Path(tmp)
        (racine / "game").mkdir(parents=True, exist_ok=True)
        if contenu is not None:
            (racine / issue1.FICHIER_SONDE).write_text(contenu)
        return racine

    def juge(self, tmp: str, contenu: str | None, fournie: bool = True) -> Metric:
        racine = self.arbre(tmp, contenu)
        donnees = frozenset({issue1.FICHIER_SONDE}) if fournie else frozenset()
        return issue1.sonde_intacte(Assay.fake(repo=str(racine), given=donnees))

    def test_la_sonde_telle_quelle_est_intacte(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrique = self.juge(tmp, issue1.SONDE.read_text())
        self.assertTrue(metrique.value)

    def test_une_assertion_desserree_est_vue(self):
        """Un octet suffit, et c'est voulu : juger « l'esprit » du test demanderait un juge."""
        with tempfile.TemporaryDirectory() as tmp:
            metrique = self.juge(tmp, issue1.SONDE.read_text() + "\n")
        self.assertFalse(metrique.value)
        self.assertIn("modifiée", metrique.reason)

    def test_une_sonde_supprimee_est_vue(self):
        with tempfile.TemporaryDirectory() as tmp:
            metrique = self.juge(tmp, None)
        self.assertFalse(metrique.value)
        self.assertIn("supprimée", metrique.reason)

    def test_une_cellule_sans_sonde_est_sans_objet_et_non_fausse(self):
        """« La sonde est intacte » n'a pas de valeur de vérité là où il n'y a pas de sonde.
        Sans `run.given`, l'absence du fichier se lirait comme une suppression."""
        with tempfile.TemporaryDirectory() as tmp:
            metrique = self.juge(tmp, None, fournie=False)
        self.assertIsNone(report({"sonde_intacte": metrique})["metrics"].get("sonde_intacte"))

    def test_le_fichier_fourni_est_bien_a_cote(self):
        """Le validateur compare l'arbre à ce fichier-ci : s'il bouge, la colonne ment."""
        self.assertTrue(issue1.SONDE.is_file(), issue1.SONDE)


class TestLaSondeDeNotation(unittest.TestCase):
    """La sonde telle que l'agent la lit, et la même telle qu'elle note.

    Un seul fichier tient les deux emplois, et `sonde_de_notation()` en réécrit la ligne
    d'import pour la notation. Ce n'est pas de la cosmétique : sans cette réécriture, une
    correction laissée dans `frame()` - là où le commentaire du dépôt l'envoie - ne se lie
    même pas, et les six colonnes se taisent ensemble sur une exécution juste. Avec une
    réécriture qui ne mord plus parce que la source a bougé, c'est pire : elle se tait sans
    le dire.
    """

    # `raquette` a été retirée de la sonde et de `GROUPES` après la campagne du n20 : ce
    # test la réclamait encore, et il échouait donc sur un état voulu du validateur. Une
    # liste écrite à la main en face d'une autre liste ne vaut que si les deux se corrigent
    # ensemble ; celle-ci est gardée parce qu'elle rend visible le retrait d'une colonne,
    # qui n'est jamais un geste de maintenance mais une décision d'expérience.
    GROUPES_ATTENDUS = ("brique", "angle", "sortie", "voisines", "traversee")

    def cas(self, texte: str) -> dict:
        """Les assertions de chaque groupe, telles qu'écrites."""
        groupes: dict[str, list[str]] = {}
        courant = None
        for ligne in texte.splitlines():
            depart = re.match(r"describe\('(\w+)'", ligne)
            if depart:
                courant = depart.group(1)
                groupes[courant] = []
            elif courant and re.match(r"\s+(test\(|assert\.|state\.(ball|bricks) =)", ligne):
                groupes[courant].append(ligne.strip())
        return groupes

    def test_la_sonde_porte_les_cinq_groupes_que_GROUPES_declare(self):
        """`rebonds()` rend une colonne par groupe. Un groupe absent de la sonde se lirait
        « aucun cas joué », donc sans objet, sur toutes les exécutions de la campagne."""
        self.assertEqual(sorted(self.cas(issue1.SONDE.read_text())), sorted(issue1.GROUPES))
        self.assertEqual(sorted(issue1.GROUPES), sorted(self.GROUPES_ATTENDUS))

    def test_la_source_importe_frame_en_direct_et_pas_le_nom_du_harnais(self):
        """`frameInterne` est l'alias que le validateur ajoute lui-même à `game/neon.js`.
        Une source qui le nommerait ferait écrire ce nom à l'agent, et le second export
        serait un doublon : le module ne compilerait plus, dans la seule cellule qui lit
        la sonde."""
        source = issue1.SONDE.read_text()
        self.assertNotIn("frameInterne", source)
        self.assertEqual(source.count(issue1.IMPORT_SOURCE), 1)

    def test_les_deux_ancres_de_la_reecriture_mordent_une_fois_et_une_seule(self):
        """La garde du même nom vit dans `sonde_de_notation()`, mais elle y lève à l'exécution,
        c'est-à-dire au milieu d'une campagne. Ici, elle casse la suite du validateur."""
        source = issue1.SONDE.read_text()
        for ancre in (issue1.IMPORT_SOURCE, issue1.ANCRE_GARDE):
            self.assertEqual(source.count(ancre), 1, ancre)

    def test_la_notation_passe_par_lalias_et_garde_sa_prise(self):
        notation = issue1.sonde_de_notation()
        self.assertIn(issue1.IMPORT_NOTATION, notation)
        self.assertNotIn(issue1.IMPORT_SOURCE, notation)
        self.assertIn(issue1.GARDE.strip(), notation)

    def test_la_notation_ne_change_aucun_cas(self):
        """La cellule qui reçoit la brique doit être notée sur ce qu'elle a lu, sinon elle
        mesure « l'agent devine-t-il un second barème » au lieu de « se corrige-t-il »."""
        self.assertEqual(
            self.cas(issue1.SONDE.read_text()),
            self.cas(issue1.sonde_de_notation()),
        )

    def test_une_source_qui_derive_leve_au_lieu_de_noter_de_travers(self):
        """Une sonde non réécrite noterait `frame` non exporté comme une correction absente.
        Se taire ici coûterait une campagne entière avant qu'on s'en aperçoive, donc la
        réécriture lève plutôt que de rendre un texte qu'elle n'a pas su corriger.

        La dérive est jouée sur une vraie source, copiée et remaniée : c'est la forme qu'elle
        prendra - quelqu'un réordonne l'import - et non un remplacement de constante."""
        derivee = issue1.SONDE.read_text().replace(issue1.IMPORT_SOURCE, "  frame as boucle,\n")
        with tempfile.TemporaryDirectory() as tmp:
            chemin = Path(tmp) / "sonde.test.js"
            chemin.write_text(derivee)
            veritable, issue1.SONDE = issue1.SONDE, chemin
            try:
                with self.assertRaises(RuntimeError) as leve:
                    issue1.sonde_de_notation()
            finally:
                issue1.SONDE = veritable
        self.assertIn("frame,", str(leve.exception))


class TestLeContratDesMetriques(unittest.TestCase):
    """Ce que le validateur rend, obtenu en l'appelant.

    Le faux ne fournit que ce que le validateur lit et refuse d'inventer le reste, donc
    cette liste **est** l'inventaire de ses dépendances : une lecture de plus fait échouer
    ce test au lieu de passer sur une valeur vide.
    """

    def run_complet(self, racine: Path) -> Assay:
        (racine / "game").mkdir(parents=True, exist_ok=True)
        (racine / issue1.FICHIER_TEST).write_text("test('a', () => {});\n")
        return Assay.fake(
            repo=str(racine),
            touched=frozenset({issue1.FICHIER_SOURCE}),
            sources_at_etalon="",
            probe={"cas": [{"groupe": cle, "ok": True} for cle in issue1.GROUPES]},
            tool_calls=(lecture(BRIQUE),),
            # Une cellule qui charge la compétence par son nom et va la lire : le prompt n'en
            # développe aucune, et c'est une mesure et non une absence de mesure. Le déclarer
            # est ce qui fait échouer ce test le jour où `skill_invoque` gagne une lecture -
            # ce qui vient d'arriver, et c'est l'information qu'on veut.
            skills_expanded=(),
        )

    def test_toutes_les_metriques_declarees_sont_produites(self):
        with tempfile.TemporaryDirectory() as tmp:
            produites = set(issue1.evaluate(self.run_complet(Path(tmp))))
        fichiers = sorted(SCENARIOS.glob("*.toml"))
        self.assertTrue(fichiers, "aucun scénario à vérifier")
        for nom in fichiers:
            scenario = tomllib.loads(nom.read_text())
            for bloc in scenario.get("validation", []):
                manquantes = set(bloc.get("metrics", ())) - produites
                self.assertEqual(manquantes, set(), f"{nom.name} déclare {manquantes}")

    def test_une_lecture_absente_ne_devient_jamais_un_faux(self):
        """Le faux ne fournit que `touched`, donc quatre métriques n'ont rien à lire.

        Aucune ne rend faux. C'est l'invariant qui compte : une mesure absente et une
        mesure ratée ne se confondent pas, et le dénominateur rétrécit visiblement au lieu
        d'enregistrer un manquement que l'agent n'a pas commis.

        Le validateur n'a plus de lecture qui *lève* - `or_unjudged` et les trois `except`
        les convertissent toutes -, donc ce test remplace celui qui attendait une
        exception : la garantie utile n'est pas qu'il refuse, c'est ce qu'il rend quand il
        ne peut pas juger.
        """
        rendu = report(issue1.evaluate(Assay.fake(touched=frozenset())))
        for nom in ("tests_ajoutes", "suite_lancee", "skill_invoque", "rebond_briques"):
            self.assertIn(nom, rendu["unjudged"], nom)
            self.assertIsNone(rendu["metrics"].get(nom), nom)

    def test_une_raison_nest_attachee_que_si_elle_dit_quelque_chose(self):
        """Une raison est publiée qu'elle porte un succès ou un échec, la base ne pouvant
        pas filtrer. C'est donc au validateur de se taire quand il n'a rien à dire."""
        with tempfile.TemporaryDirectory() as tmp:
            rendu = report(issue1.evaluate(self.run_complet(Path(tmp))))
        self.assertTrue(rendu["metrics"]["delivered"])
        self.assertNotIn("delivered", rendu["reasons"])
        # Celle-là, en revanche, dit quelle compétence a été lue même en succès : c'est ce
        # qui rend la colonne lisible quand plusieurs briques peuvent la faire passer.
        self.assertIn("skill_invoque", rendu["reasons"])


if __name__ == "__main__":
    unittest.main()
