#!/usr/bin/env python3
"""Apply the approved 18-question freeze to data/questions/questions.json.

Wording basis: the statements Martin approved in the freeze packet
(docs/03-QUESTION-FREEZE.md + data/questions/freeze-proposal.json), which are
byte-identical to the pool statements in questions.json for those 18 ids. That is
also the wording the live codings (data/codings/<party>.json, v0.9-prefreeze) were
coded against -- CODING-PROMPT.md requires the published statement to be the
statement the coder answered.

Writes the 18 with status "frozen" (schema: id, statement, topic, dimensions,
status, notes) and leaves the pool only in the retired v2 file.
"""
import json, os, sys

BASE = '.'
QDIR = os.path.join(BASE, 'data/questions')

pool = json.load(open(os.path.join(QDIR, 'pool/questions.v1.all54.json')))
prop = json.load(open(os.path.join(QDIR, 'freeze-proposal.json')))
frozen_ids = [p['id'] for p in prop]

order = {q['id']: i for i, q in enumerate(pool)}
missing = [i for i in frozen_ids if i not in order]
if missing:
    sys.exit('frozen id(s) not in pool: %s' % missing)

byname = {q['id']: q for q in pool}
out = []
for qid in sorted(frozen_ids, key=lambda i: order[i]):
    p = byname[qid]
    out.append({
        'id': qid,
        'statement': p['statement'],
        'topic': p['topic'],
        'dimensions': p['dimensions'],
        'status': 'frozen',
        'notes': p['notes'],
    })

# sanity: exactly 3 per topic, 6 topics, ids match the proposal
from collections import Counter
c = Counter(q['topic'] for q in out)
assert len(out) == 18 and len(c) == 6 and set(c.values()) == {3}, c
assert sorted(q['id'] for q in out) == sorted(frozen_ids)

with open(os.path.join(QDIR, 'questions.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
    f.write('\n')

print('wrote %d frozen questions' % len(out))
print('ids:', [q['id'] for q in out])
print('topics:', dict(c))
