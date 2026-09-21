// reporter.mjs - the reporter that renders the cases of `probe.test.js` as JSON on stdout.
//
// `probe.test.js` is an ordinary test file, run by `node --test` like the suite of the repo, and
// `node --test` only prints text for humans. Its result therefore has to be translated into what
// `trysquare` reads, and that happens here, plugged in through `--test-reporter`: the probe
// writes nothing, prints nothing and knows nothing about this format. All the measuring
// machinery is on this side, all the domain is on the other.
//
// Output: `{"cases": [{"group", "name", "ok", "detail"}, ...]}`, one object per `test()`, with
// the enclosing `describe()` as its group. `{"error": "..."}` when no case ran at all, which
// `validators/issue1.py` reads as "I could not judge".
//
// This reporter runs in the parent process, while the tests run in a child. That is what spares
// the probe from gagging `console.log`: whatever the agent's code prints arrives as `test:stdout`
// and is dropped here, without the measured file having to deal with it.

export default async function* report(events) {
  const cases = [];
  // The name of the open `describe`, by nesting level. `test:start` comes before the cases it
  // contains, so the group of a case is whatever is open just above it.
  const groups = [];
  const noise = [];

  for await (const { type, data } of events) {
    switch (type) {
      case 'test:start':
        groups[data.nesting] = data.name;
        break;

      case 'test:pass':
      case 'test:fail':
        // The `describe`s and the file itself come through here too: they carry the aggregated
        // verdict of their children, which is already counted.
        if (data.details?.type === 'suite' || data.nesting < 1) break;
        cases.push({
          group: groups[data.nesting - 1] || '',
          name: data.name,
          ok: type === 'test:pass',
          detail: why(data.details?.error),
        });
        break;

      case 'test:diagnostic':
        // `t.diagnostic()` arrives after the verdict of the case that emitted it. It carries
        // where a correct fix came from ("deflected by step()"), so it completes the detail
        // rather than replacing it. At level 0 it is the summary of `node --test` ("tests 9",
        // "pass 9") and not a case.
        if (data.nesting >= 1 && cases.length) {
          const last = cases[cases.length - 1];
          last.detail = [last.detail, data.message].filter(Boolean).join(' ; ');
        }
        break;

      case 'test:stderr':
        noise.push(data.message);
        break;
    }
  }

  // No case at all: the file could not load. Either a `throw` from the probe because it did not
  // find its grip on the module, or agent code that does not evaluate. Both are said the same
  // way, because in both cases the probe has nothing to say about the correction.
  yield `${JSON.stringify(cases.length ? { cases } : { error: reason(noise) })}\n`;
}

// The detail of a case: the message of the assertion as the probe wrote it. An exception that is
// not an assertion is something else - the probe touched a module that does not do what it
// thinks - and is said as such.
//
// `node:test` wraps whatever the case threw in an `ERR_TEST_FAILURE` error and puts the original
// in `cause`. Without unwrapping it, everything is an "exception", assertions included, and the
// distinction stops meaning anything.
function why(error) {
  if (!error) return '';
  const thrown = error.code === 'ERR_TEST_FAILURE' && error.cause ? error.cause : error;
  const message = thrown.message || error.message || String(thrown);
  return thrown.code === 'ERR_ASSERTION' ? message : `exception: ${message}`;
}

// The message of the crash, read from stderr. The error line first, because node prefixes its own
// with the offending source fragment and because the message is what makes sense in a table. The
// call stack is dropped: this is not a crash report.
function reason(noise) {
  const lines = noise
    .join('')
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith('at '));
  const said = lines.find((l) => /^\w*Error\b/.test(l));
  return said || lines.slice(-3).join(' ; ') || 'no case ran';
}
