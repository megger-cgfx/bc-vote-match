import json, os, collections
ROOT = '.'
for p in ['ndp','cpb','green','onebc','centrebc']:
    sp = f'{ROOT}/data/raw/{p}/sources.json'
    d = json.load(open(sp))
    byurl = collections.defaultdict(list)
    for s in d:
        byurl[s.get('url','')].append(s['id'])
    du = {u: ids for u, ids in byurl.items() if len(ids) > 1}
    byid = collections.defaultdict(list)
    for s in d:
        byid[s['id']].append(s.get('url',''))
    di = {i: us for i, us in byid.items() if len(us) > 1}
    print(f'--- {p}: {len(d)} records; dup-urls={len(du)}; dup-ids={len(di)}')
    for u, ids in list(du.items())[:20]:
        print('   dupURL', ids, u[:100])
    for i, us in list(di.items())[:20]:
        print('   dupID ', i, [x[:70] for x in us])
