import json, os
ROOT = '.'
for p in ['ndp','cpb','green','onebc','centrebc']:
    fp = f'{ROOT}/data/raw/{p}/sources.json'
    print(f'===== {p} =====')
    if not os.path.exists(fp):
        print('  MISSING'); continue
    d = json.load(open(fp))
    for s in d:
        lp = s.get('local_path') or ''
        ex = os.path.exists(os.path.join(ROOT, lp)) if lp else False
        tp = s.get('text_path') or ''
        tex = os.path.exists(os.path.join(ROOT, tp)) if tp else False
        print(f"  {s['id']:12} {s.get('type',''):9} txt={str(tex):5} {s.get('published','')} | {s.get('title','')[:60]}")
        print(f"      url={s.get('url','')}")
        print(f"      arch={s.get('archive_url')}")
