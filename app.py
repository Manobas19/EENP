import json
import pandas as pd
import plotly.express as px
import streamlit as st
from core import *

st.set_page_config(page_title='EENP 1.0 | Research Studio',page_icon='🧬',layout='wide')
st.markdown('''<style>
.block-container {padding-top:2rem} 
.hero {background:linear-gradient(115deg,#123e84,#078b91 55%,#7c3aed);padding:30px;border-radius:24px;color:white;margin-bottom:22px;box-shadow:0 12px 30px #123e8422}
.hero h1 {color:white;font-size:2.8rem;margin:0}.hero p{color:#e0f2fe;font-size:1.1rem}
[data-testid="stMetric"]{background:white;padding:18px;border-radius:16px;border-top:4px solid #14b8a6;box-shadow:0 4px 18px #1725540a}
</style><div class="hero"><h1>🧬 EENP 1.0</h1><p>Endogenous–Exogenous Interaction Network • Research Studio</p>INTEGRATE &nbsp; • &nbsp; CONNECT &nbsp; • &nbsp; DISCOVER &nbsp; • &nbsp; EXPLORE</div>''',unsafe_allow_html=True)
st.caption('Concept based on the supplied EENP poster. Independent computational prototype; not an implementation validated by its inventor.')
st.warning('Research prototype • Default data are entirely synthetic • No trained AI, clinical predictions, or treatment recommendations.')
modules=['01 · Biological context','02 · Identity & data harmonization','03 · Evidence & provenance','04 · Dual-state network','05 · Cross-domain bridges','06 · Interaction asymmetry','07 · Competing mechanisms','08 · Perturbation & recovery','09 · Uncertainty','10 · Next evidence','11 · Cross-context comparison','12 · Reproducible package']
with st.sidebar:
    st.title('🔬 Research workspace')
    page=st.radio('Architecture',modules)
    mode=st.radio('Evidence source',['Synthetic demo','Upload CSV'])
    upload=st.file_uploader('Evidence CSV',type=['csv']) if mode=='Upload CSV' else None
    st.download_button('Download example CSV',demo().to_csv(index=False),'example_evidence.csv','text/csv')
try:
    if mode=='Upload CSV' and upload is None:
        st.info('Upload an evidence CSV or choose Synthetic demo.');st.stop()
    raw=validate(pd.read_csv(upload) if upload is not None else demo())
except Exception as exc:
    st.error(str(exc));st.stop()
with st.sidebar:
    context={}
    remaining=raw
    for c in CONTEXT:
        context[c]=st.selectbox(c.title(),sorted(remaining[c].unique()))
        remaining=remaining[remaining[c].eq(context[c])]
    threshold=st.slider('Minimum evidence confidence',0.,1.,.3,.05)
    st.caption('Confidence values are supplied by the data author; they are not calibrated probabilities.')
df=select(raw,context,threshold)
if df.empty:
    st.info('No evidence passes these filters. Lower the confidence threshold.');st.stop()
g=graph(df);edges=aggregate(df);nodes=sorted(g)
cols=st.columns(4)
for col,label,val in zip(cols,['Entities','Evidence records','Directed connections','Cross-domain links'],[len(g),len(df),len(edges),sum(g.nodes[a]['domain']!=g.nodes[b]['domain'] for a,b in g.edges)]): col.metric(label,val)
st.subheader(page)
if page==modules[0]:
    st.json(context)
    st.info('Filters match tissue, species and disease exactly. Dose, time, cell type and genotype are recorded below as study metadata only; this prototype does not infer their effects.')
    for field in ['Cell type','Genotype','Exposure / dose and units','Observation time and units']:
        st.text_input(field,key='meta_'+field)
elif page==modules[1]:
    st.write('Whitespace is trimmed, exact duplicates removed, numeric ranges checked, and conflicting entity domains rejected. IDs remain case-sensitive.')
    st.info('Use curated canonical identifiers. Automatic gene/protein synonym resolution, ontology mapping and species orthology are not implemented.')
    st.dataframe(raw,use_container_width=True)
    st.code(', '.join(REQUIRED))
elif page==modules[2]:
    st.dataframe(df,use_container_width=True)
    st.plotly_chart(px.histogram(df,x='method',color='source_domain',color_discrete_sequence=['#0d9488','#9333ea']),use_container_width=True)
    st.caption('References are preserved as supplied; their authenticity is not automatically verified.')
elif page==modules[3]:
    st.plotly_chart(network_figure(df),use_container_width=True)
    st.caption('Arrows indicate direction. Teal edges: positive net effect; pink: negative; gray: cancellation. Zero-weight edges remain evidence connections.')
elif page==modules[4]:
    cross=edges[[g.nodes[r.source]['domain']!=g.nodes[r.target]['domain'] for r in edges.itertuples()]]
    st.dataframe(cross,use_container_width=True)
    st.caption('Direct bridges between domains in the selected evidence. Explore indirect connections in Competing mechanisms.')
elif page==modules[5]:
    rows=[]
    for r in edges.itertuples():
        reverse=g.get_edge_data(r.target,r.source)
        rows.append({'source':r.source,'target':r.target,'forward_weight':r.weight,'reverse_weight':reverse['weight'] if reverse else None,'reverse_evidence':'present' if reverse else 'missing'})
    st.dataframe(pd.DataFrame(rows),use_container_width=True)
    st.info('Missing reverse evidence does not prove the reverse biological effect is absent.')
elif page==modules[6]:
    a,b=st.columns(2)
    source=a.selectbox('Starting entity',nodes);target=b.selectbox('Destination entity',nodes,index=len(nodes)-1)
    hops=st.slider('Maximum pathway length',1,6,4)
    if source==target: st.info('Choose two different entities. Feedback cycles are not enumerated.')
    else:
        result=paths(df,source,target,hops)
        if result.empty: st.info('No directed path within this length limit.')
        else: st.dataframe(result,use_container_width=True)
    st.caption('Up to 100 simple paths in traversal order. Signed products are heuristic model weights, not mechanism probabilities or causal proof.')
elif page==modules[7]:
    selected=st.multiselect('Perturb entities',nodes,default=[nodes[0]])
    interventions={n:st.slider('Input: '+n,-1.,1.,.5,.1) for n in selected}
    pulse=st.slider('Input duration (steps)',1,30,10)
    gain=st.slider('Propagation gain',0.,.95,.6,.05)
    trajectory=simulate(df,interventions,40,pulse,gain)
    st.plotly_chart(px.line(trajectory,labels={'value':'Model response (arbitrary units)','index':'Step'},color_discrete_sequence=px.colors.qualitative.Vivid),use_container_width=True)
    st.caption('Zero initial state and zero unperturbed baseline. Input stops after the chosen duration. Multiple inputs are simulated together. This is a bounded toy dynamical system, not a biological dose-response model.')
    st.session_state['last_sim']={'context':context,'threshold':threshold,'interventions':interventions,'steps':40,'pulse':pulse,'gain':gain}
    st.latex(r'x_{t+1}=\tanh(g\,\widetilde{W}x_t+u_t)')
elif page==modules[8]:
    st.dataframe(edges.sort_values('disagreement',ascending=False),use_container_width=True)
    st.plotly_chart(px.scatter(edges,x='confidence',y='disagreement',size='evidence_count',hover_name='source',color='disagreement',color_continuous_scale='Plasma'),use_container_width=True)
    st.caption('Disagreement = 1 − |sum(signed confidence)| / sum(confidence). This measures directional conflict, not statistical uncertainty. Zero-confidence records supply no directional information.')
elif page==modules[9]:
    ranked=edges.copy()
    ranked['priority']=(1-ranked.confidence+ranked.disagreement)/(1+ranked.evidence_count)
    st.dataframe(ranked.sort_values('priority',ascending=False),use_container_width=True)
    st.info('Heuristic prioritization of existing links only: (1 − mean confidence + disagreement) / (1 + record count). Cost, feasibility, missing links and expected information gain are not modeled.')
elif page==modules[10]:
    alternative={}
    for c in CONTEXT: alternative[c]=st.selectbox('Comparison '+c,sorted(raw[c].unique()),key='alt_'+c)
    other=aggregate(select(raw,alternative,threshold))
    if alternative==context: st.info('Select a different context to make a meaningful comparison.')
    if other.empty: st.info('No matching comparison evidence.')
    else:
        merged=edges.merge(other,on=['source','target'],how='outer',suffixes=('_current','_comparison'),indicator=True)
        intersection=int(merged['_merge'].eq('both').sum())
        st.metric('Directed edge Jaccard overlap',f'{intersection/len(merged):.2f}')
        st.dataframe(merged,use_container_width=True)
        st.caption('Descriptive overlap and weight comparison only. No cross-context predictive transfer validation is performed.')
else:
    params=st.session_state.get('last_sim',{'context':context,'threshold':threshold,'interventions':{nodes[0]:.5},'steps':40,'pulse':10,'gain':.6})
    if params['context']!=context or params['threshold']!=threshold or any(n not in g for n in params['interventions']):
        params={'context':context,'threshold':threshold,'interventions':{nodes[0]:.5},'steps':40,'pulse':10,'gain':.6}
        st.info('Filters changed. Export uses the displayed default simulation settings.')
    st.json(params)
    result=simulate(df,params['interventions'],params['steps'],params['pulse'],params['gain'])
    metadata={k:v for k,v in st.session_state.items() if k.startswith('meta_')}
    st.download_button('📦 Download reproducible evidence package',package(df,context,{**params,'study_metadata':metadata},result),'EENP_results.zip','application/zip')
    st.download_button('Download complete imported evidence',raw.to_csv(index=False),'all_evidence.csv','text/csv')
    st.caption('ZIP includes filtered evidence, aggregated edges, simulation, parameters, software versions and evidence checksum. Keep the source-code bundle alongside it.')
