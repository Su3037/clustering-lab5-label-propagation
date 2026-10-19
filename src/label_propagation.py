#!/usr/bin/env python3
"""Independent Python reference for the Lab05 teaching model (MIT).

Undirected simple graph, positive weights. Async/sync, min/max/current-first ties.
Default counting includes the final zero-change verification sweep.
"""
import argparse,json,math
from pathlib import Path

def solve(nodes,edges,*,mode='async',order=None,tie='min',max_iters=50):
    if len(set(nodes))!=len(nodes) or not nodes:raise ValueError('nodes must be nonempty and unique')
    if mode not in ('async','sync') or tie not in ('min','max','keep'):raise ValueError('unknown mode or tie rule')
    if not isinstance(max_iters,int) or max_iters<1:raise ValueError('max_iters must be positive')
    seq=list(order) if order is not None else sorted(nodes)
    if len(seq)!=len(nodes) or set(seq)!=set(nodes):raise ValueError('order must visit every node exactly once')
    adj={n:[] for n in nodes};seen_edges=set()
    for u,v,w in edges:
        key=tuple(sorted((u,v)))
        if u not in adj or v not in adj or u==v or key in seen_edges:raise ValueError('invalid or duplicate edge')
        if not isinstance(w,(int,float)) or not math.isfinite(w) or w<=0:raise ValueError('weights must be positive and finite')
        adj[u].append((v,w));adj[v].append((u,w));seen_edges.add(key)
    labels={n:n for n in nodes};seen={tuple(labels[n] for n in nodes):0};events=[];status='limit'
    for iteration in range(1,max_iters+1):
        old=dict(labels);pending=dict(labels);changes=0
        for vertex in seq:
            source=old if mode=='sync' else labels
            votes={}
            for neighbor,weight in adj[vertex]:
                label=source[neighbor];votes[label]=votes.get(label,0)+weight
            previous=source[vertex];winner=previous
            if votes:
                maximum=max(votes.values());candidates=sorted(k for k,v in votes.items() if abs(v-maximum)<1e-12)
                winner=previous if tie=='keep' and previous in candidates else candidates[-1] if tie=='max' else candidates[0]
            if winner!=previous:changes+=1
            pending[vertex]=winner
            if mode=='async':labels[vertex]=winner
            events.append({'round':iteration,'node':vertex,'old':previous,'label':winner,'votes':votes})
        if mode=='sync':labels=pending
        signature=tuple(labels[n] for n in nodes)
        if not changes:status='stable';break
        if signature in seen:status='cycle';break
        seen[signature]=iteration
    groups={}
    for n,label in labels.items():groups.setdefault(label,[]).append(n)
    cut=sum(w for u,v,w in edges if labels[u]!=labels[v])
    return {'labels':labels,'rounds':iteration,'status':status,'cut':cut,'clusters':groups,'events':events}

def label_propagation(nodes,edges,max_iters=50,order=None):
    """Course-compatible API: label_propagation(...) -> (labels, iters)."""
    r=solve(nodes,edges,max_iters=max_iters,order=order)
    return r['labels'],r['rounds']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('graph',type=Path);p.add_argument('--mode',choices=['async','sync'],default='async')
    p.add_argument('--tie',choices=['min','max','keep'],default='min');p.add_argument('--order',nargs='+');p.add_argument('--max-iters',type=int,default=50)
    a=p.parse_args();g=json.loads(a.graph.read_text(encoding='utf-8'))
    edges=[(e['u'],e['v'],e['w']) if isinstance(e,dict) else tuple(e) for e in g['edges']]
    print(json.dumps(solve(g['nodes'],edges,mode=a.mode,tie=a.tie,order=a.order,max_iters=a.max_iters),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
