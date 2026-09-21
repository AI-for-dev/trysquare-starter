// rapport.mjs - le rapporteur qui rend les cas de `sonde.test.js` en JSON sur stdout.
//
// `sonde.test.js` est un fichier de test ordinaire, lancé par `node --test` comme la suite
// du dépôt, et `node --test` n'imprime que du texte pour humains. Il faut donc traduire son
// résultat dans ce que `trysquare` lit, et c'est ici, branché par `--test-reporter` : la
// sonde n'écrit rien, n'imprime rien et ne connaît pas ce format. Toute la mécanique de
// mesure est de ce côté, tout le domaine est de l'autre.
//
// Rendu : `{"cas": [{"groupe", "nom", "ok", "detail"}, ...]}`, un objet par `test()`, avec
// le `describe()` qui l'englobe pour groupe. `{"erreur": "..."}` quand aucun cas n'a été
// joué, ce que `validateurs/issue1.py` lit comme « je n'ai pas pu juger ».
//
// Ce rapporteur tourne dans le processus parent, alors que les tests tournent dans un
// enfant. C'est ce qui dispense la sonde de bâillonner `console.log` : ce que le code de
// l'agent imprime arrive en `test:stdout` et se jette d'ici, sans que le fichier mesuré ait
// à s'en occuper.

export default async function* rapporter(evenements) {
  const cas = [];
  // Le nom du `describe` ouvert, par niveau d'imbrication. `test:start` passe avant les
  // cas qu'il contient, donc le groupe d'un cas est ce qui est ouvert juste au-dessus.
  const groupes = [];
  const bruit = [];

  for await (const { type, data } of evenements) {
    switch (type) {
      case 'test:start':
        groupes[data.nesting] = data.name;
        break;

      case 'test:pass':
      case 'test:fail':
        // Les `describe` et le fichier lui-même repassent ici : ils portent le verdict
        // agrégé de leurs enfants, qui est déjà compté.
        if (data.details?.type === 'suite' || data.nesting < 1) break;
        cas.push({
          groupe: groupes[data.nesting - 1] || '',
          nom: data.name,
          ok: type === 'test:pass',
          detail: pourquoi(data.details?.error),
        });
        break;

      case 'test:diagnostic':
        // `t.diagnostic()` arrive après le verdict du cas qui l'a émis. Il porte la
        // provenance d'une correction juste (« dévié par step() »), donc il complète le
        // détail plutôt que de le remplacer. Au niveau 0 c'est le résumé de `node --test`
        // (« tests 9 », « pass 9 ») et non un cas.
        if (data.nesting >= 1 && cas.length) {
          const dernier = cas[cas.length - 1];
          dernier.detail = [dernier.detail, data.message].filter(Boolean).join(' ; ');
        }
        break;

      case 'test:stderr':
        bruit.push(data.message);
        break;
    }
  }

  // Aucun cas : le fichier n'a pas pu se charger. Un `throw` de la sonde parce qu'elle n'a
  // pas trouvé sa prise dans le module, ou du code de l'agent qui ne s'évalue pas. Les
  // deux se disent de la même façon, parce que dans les deux cas la sonde n'a rien à dire
  // sur la correction.
  yield `${JSON.stringify(cas.length ? { cas } : { erreur: raison(bruit) })}\n`;
}

// Le détail d'un cas : le message de l'assertion telle que la sonde l'a écrite. Une
// exception qui n'est pas une assertion est autre chose - la sonde a touché un module qui ne
// fait pas ce qu'elle croit - et se dit comme telle.
//
// `node:test` enveloppe ce que le cas a jeté dans une erreur `ERR_TEST_FAILURE` et met
// l'originale dans `cause`. Sans la déballer, tout est « exception », y compris les
// assertions, et la distinction ne veut plus rien dire.
function pourquoi(erreur) {
  if (!erreur) return '';
  const jetee = erreur.code === 'ERR_TEST_FAILURE' && erreur.cause ? erreur.cause : erreur;
  const message = jetee.message || erreur.message || String(jetee);
  return jetee.code === 'ERR_ASSERTION' ? message : `exception : ${message}`;
}

// Le message du plantage, lu dans stderr. La ligne d'erreur d'abord, parce que node fait
// précéder la sienne du fragment de source fautif et que c'est le message qui a du sens
// dans une table. La trace d'appels est jetée : ce n'est pas un rapport de plantage.
function raison(bruit) {
  const lignes = bruit
    .join('')
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith('at '));
  const dite = lignes.find((l) => /^\w*Error\b/.test(l));
  return dite || lignes.slice(-3).join(' ; ') || 'aucun cas joué';
}
