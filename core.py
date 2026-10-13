"""EENP exploratory network engine. All default evidence is synthetic."""
import io, json, hashlib, zipfile, platform
import numpy as np
import pandas as pd
import networkx as nx
import plotly.graph_objects as go

CONTEXT = ['tissue','species','disease']
REQUIRED = ['source','target','source_domain','target_domain','effect','confidence','reference','method'] + CONTEXT

def demo():
    pairs = [('Compound_A','Gene_A','exogenous','endogenous',1,.9),('Compound_A','Gene_B','exogenous','endogenous',-1,.8),('Exposure_B','Gene_B','exogenous','endogenous',1,.7),('Gene_A','Protein_A','endogenous','endogenous',1,.95),('Gene_B','Protein_A','endogenous','endogenous',-1,.75),('Protein_A','Pathway_A','endogenous','endogenous',1,.85),('Pathway_A','Outcome_A','endogenous','endogenous',1,.8),('Protein_A','Compound_A','endogenous','exogenous',-1,.6),('Compound_A','Gene_A','exogenous','endogenous',-1,.4),('Exposure_B','Pathway_A','exogenous','endogenous',-1,.55)]
    rows=[]
    for tissue in ['Tissue_A','Tissue_B']:
        for i,p in enumerate(pairs):
            s,t,sd,td,e,c=p
            if tissue=='Tissue_B' and i in [2,7]: continue
            rows.append([s,t,sd,td, -e if tissue=='Tissue_B' and i==3 else e,c,'SYNTHETIC-'+str(i),'synthetic',tissue,'demo_species','demo_condition'])
    return pd.DataFrame(rows,columns=REQUIRED)

def validate(df):
    missing=set(REQUIRED)-set(df.columns)
    if missing: raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    if df.empty: raise ValueError('The evidence file is empty.')
    if len(df)>5000: raise ValueError('Prototype limit: 5,000 evidence rows.')
    df=df.copy()
    for c in REQUIRED:
        if df[c].isna().any(): raise ValueError(f'{c}: missing values are not allowed.')
        if c not in ['effect','confidence']:
            df[c]=df[c].astype(str).str.strip()
            if df[c].eq('').any(): raise ValueError(f'{c}: blank values are not allowed.')
    for c in ['effect','confidence']: df[c]=pd.to_numeric(df[c],errors='raise')
    if not df.effect.isin([-1,1]).all(): raise ValueError('effect must be +1 or -1; unknown direction must be curated before import.')
    if not np.isfinite(df.confidence).all() or not df.confidence.between(0,1).all(): raise ValueError('confidence must be finite and in [0,1].')
    domains={}
    for side in ['source','target']:
        for n,d in zip(df[side],df[side+'_domain']):
            if d not in ['endogenous','exogenous']: raise ValueError('Domains must be endogenous or exogenous.')
            if n in domains and domains[n]!=d: raise ValueError(f'Conflicting domains for {n}.')
            domains[n]=d
    if len(domains)>150: raise ValueError('Prototype limit: 150 nodes.')
    return df.drop_duplicates().reset_index(drop=True)

def select(df,context,threshold=0):
    mask=df.confidence.ge(threshold)
    for c,v in context.items(): mask &= df[c].eq(v)
    return df.loc[mask].copy()

def aggregate(df):
    rows=[]
    for (s,t),g in df.groupby(['source','target'],sort=True):
        total=g.confidence.sum(); signed=(g.effect*g.confidence).sum()
        rows.append(dict(source=s,target=t,weight=float(signed/len(g)),confidence=float(g.confidence.mean()),disagreement=float(1-abs(signed)/total) if total else 0.,evidence_count=len(g)))
    return pd.DataFrame(rows,columns=['source','target','weight','confidence','disagreement','evidence_count'])

def graph(df):
    g=nx.DiGraph()
    for r in df.itertuples():
        g.add_node(r.source,domain=r.source_domain);g.add_node(r.target,domain=r.target_domain)
    for r in aggregate(df).itertuples(): g.add_edge(r.source,r.target,weight=r.weight)
    return g

def network_figure(df):
    g=graph(df);pos=nx.spring_layout(g,seed=42)
    fig=go.Figure()
    for a,b,d in g.edges(data=True):
        x,y=pos[a];u,v=pos[b]
        color='#0d9488' if d['weight']>0 else '#e11d48' if d['weight']<0 else '#94a3b8'
        fig.add_trace(go.Scatter(x=[x,u],y=[y,v],mode='lines',line=dict(color=color,width=1+3*abs(d['weight'])),hoverinfo='text',text=f'{a} → {b}: {d["weight"]:.2f}',showlegend=False))
        fig.add_annotation(x=u*.85+x*.15,y=v*.85+y*.15,ax=u*.65+x*.35,ay=v*.65+y*.35,xref='x',yref='y',axref='x',ayref='y',showarrow=True,arrowhead=2,arrowcolor=color,text='')
    for domain,color in [('endogenous','#0d9488'),('exogenous','#9333ea')]:
        ns=[n for n in g if g.nodes[n]['domain']==domain]
        fig.add_trace(go.Scatter(x=[pos[n][0] for n in ns],y=[pos[n][1] for n in ns],text=ns,mode='markers+text',textposition='top center',marker=dict(size=22,color=color,line=dict(width=2,color='white')),name=domain))
    fig.update_layout(height=550,template='plotly_white',xaxis=dict(visible=False),yaxis=dict(visible=False),margin=dict(l=20,r=20,t=25,b=20),legend=dict(orientation='h'))
    return fig

def simulate(df,interventions,steps=30,pulse=10,gain=.6):
    g=graph(df);nodes=sorted(g);idx={n:i for i,n in enumerate(nodes)}
    w=np.zeros((len(nodes),len(nodes)))
    for a,b,d in g.edges(data=True): w[idx[b],idx[a]]=d['weight']
    w=w/max(1.,np.abs(w).sum(axis=1).max(initial=0))
    x=np.zeros(len(nodes));u=np.zeros(len(nodes))
    for n,v in interventions.items():
        if n not in idx: raise ValueError('Intervention node missing: '+n)
        u[idx[n]]=v
    result=[x.copy()]
    for t in range(steps):
        x=np.tanh(gain*w@x+(u if t<pulse else 0));result.append(x.copy())
    return pd.DataFrame(result,columns=nodes).rename_axis('step')

def paths(df,source,target,max_hops=5):
    g=graph(df);rows=[]
    # Bounded depth and output for predictable interactive runtime.
    for p in nx.all_simple_paths(g,source,target,cutoff=max_hops):
        ws=[g[a][b]['weight'] for a,b in zip(p,p[1:])]
        rows.append({'path':' → '.join(p),'signed_product':float(np.prod(ws)),'hops':len(ws)})
        if len(rows)>=100: break
    return pd.DataFrame(rows)

def package(df,context,params,trajectory):
    buf=io.BytesIO();raw=df.to_csv(index=False)
    manifest={'prototype':'EENP 1.0 research prototype','context':context,'parameters':params,'evidence_sha256':hashlib.sha256(raw.encode()).hexdigest(),'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'networkx':nx.__version__,'limitations':'Synthetic default data. No trained AI or clinical validation. Context transfer is edge overlap, not predictive validation. Simulation units are arbitrary.'}
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('evidence.csv',raw);z.writestr('aggregated_edges.csv',aggregate(df).to_csv(index=False));z.writestr('simulation.csv',trajectory.to_csv());z.writestr('manifest.json',json.dumps(manifest,indent=2))
    return buf.getvalue()
