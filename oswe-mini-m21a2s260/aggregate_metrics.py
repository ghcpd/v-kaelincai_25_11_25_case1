import json
def read(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return []

pre=read('results/results_pre.json')
post=read('results/results_post.json')

def percentile(data, p):
    if not data: return 0
    s=sorted(data)
    k=(len(s)-1)*(p/100)
    f=int(k)
    c=min(f+1,len(s)-1)
    if f==c: return s[int(k)]
    d=k-f
    return s[f]*(1-d)+s[c]*d

def stats(arr):
    if not arr: return {'count':0}
    t=[x.get('duration_ms',0) for x in arr]
    return {'count':len(t),'p50':float(percentile(t,50)),'p95':float(percentile(t,95))}

metrics={'pre':stats(pre),'post':stats(post)}
with open('results/aggregated_metrics.json','w') as f:
    json.dump(metrics,f,indent=2)
print('Metrics written')
