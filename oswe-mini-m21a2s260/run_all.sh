@echo off
setlocal
echo Running Pre-Change tests
cd Project_A_PreChange
call run_tests.sh
cd ..
echo Running Post-Change tests
cd Project_B_PostChange
call run_tests.sh
cd ..
echo Aggregating results
python - <<"PY"
import json,os
pre='Project_A_PreChange/results/results_pre.json'
post='Project_B_PostChange/results/results_post.json'
outdir='results'
os.makedirs(outdir,exist_ok=True)
res={'pre':[], 'post':[]}
try:
    with open(pre) as f: res['pre']=json.load(f)
except: res['pre']=[]
try:
    with open(post) as f: res['post']=json.load(f)
except: res['post']=[]
with open(os.path.join(outdir,'results_pre.json'),'w') as f: json.dump(res['pre'],f,indent=2)
with open(os.path.join(outdir,'results_post.json'),'w') as f: json.dump(res['post'],f,indent=2)
with open(os.path.join(outdir,'aggregated_metrics.json'),'w') as f:
    json.dump({'pre_count':len(res['pre']),'post_count':len(res['post'])},f,indent=2)
print('Done')
PY
echo Aggregating metrics
python aggregate_metrics.py
echo Building compare_report.md
python - <<"PY"
import json
pre='results/results_pre.json'
post='results/results_post.json'
with open(pre) as f: p=json.load(f)
with open(post) as f: q=json.load(f)
lines=['# Compare Report','\n']
lines.append('## Summary')
lines.append(f'- Pre cases: {len(p)}\n- Post cases: {len(q)}')
lines.append('\n## Per-case results')
for a,b in zip(p,q):
    lines.append(f'- {a.get("id")} | pre: {a.get("parsed")} | post: {b.get("parsed")}')
open('compare_report.md','w').write('\n'.join(lines))
print('Report written')
PY
echo Done.
