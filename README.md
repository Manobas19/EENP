# EENP 1.0 — colorful research prototype

Based on the 12-layer concept in the supplied poster. This is an independent exploratory implementation, not a scientifically validated reproduction. All default entities, contexts and evidence are synthetic. No API key required for analysis. No trained AI model, clinical prediction, literature retrieval or treatment recommendations are included.

## Start in Google Colab
1. Open https://colab.research.google.com/ and choose File → Upload notebook.
2. Upload EENP_All_12_Layers_Colab.ipynb, included in this ZIP.
3. Run cells from the top. The notebook writes the complete app and engine itself; no ZIP upload is needed.
4. All 12 analysis layers work directly in the notebook. Open the table of contents to navigate them. Set USE_UPLOAD=True to use a curated real-evidence CSV. Automatic database retrieval is not implemented. Optional final cells launch Streamlit using ngrok. For these, create an ngrok account and add NGROK_AUTHTOKEN to Colab Secrets (key icon). Enable notebook access. The resulting URL is temporary and public; use synthetic/non-sensitive data. Stop the tunnel when finished.

## Start Streamlit locally (Python 3.10+)
Unzip this package, open a terminal inside the EENP folder, then run:

    python -m pip install -r requirements.txt
    python -m streamlit run app.py

Open the localhost URL printed by Streamlit. For Streamlit Community Cloud, upload app.py, core.py, requirements.txt and .streamlit/config.toml to a GitHub repository; choose app.py as the entry point. This project does not contain user authentication or a patient-data backend.

## Your own evidence
Select Upload CSV in the sidebar. Start from example_evidence.csv. Each row is one directed evidence record. Required columns:

- source, target: canonical entity identifiers (case-sensitive).
- source_domain, target_domain: endogenous or exogenous.
- effect: 1 for positive, -1 for negative; curate unknown effects separately.
- confidence: author-supplied score from 0 to 1, not a calibrated probability.
- reference: traceable publication/database identifier; not automatically verified.
- method: experimental/computational method or synthetic.
- tissue, species, disease: exact context labels.

Optional columns are preserved. Limits: 5,000 rows and 150 nodes. Exact duplicate rows are removed; other records are not assumed independent. Curate correlated studies before interpretation. Context filters match exactly. No inferred synonym/ortholog mapping. Dose, time, genotype and cell type are metadata only.

## Model and layer scope
1 Context: exact tissue/species/disease filters plus metadata.
2 Harmonization: whitespace, duplicates, schema, domains and range checks; no automatic ID mapping.
3 Provenance: row-level evidence and reference display; no source verification.
4 Dual-state graph: directed network with endogenous/exogenous node colors.
5 Bridges: direct cross-domain links; indirect paths in layer 7.
6 Asymmetry: forward and reverse evidence, preserving missingness.
7 Mechanisms: up to 100 simple paths, max 6 hops; no feedback-cycle enumeration.
8 Simulation: zero-state tanh propagation with temporary, simultaneous inputs.
9 Uncertainty: weighted directional disagreement; no calibrated intervals.
10 Next evidence: explicit heuristic ranking; not experimental optimization.
11 Transfer: descriptive context overlap; no predictive validation.
12 Package: CSVs, manifest, checksum and software versions.

For each directed pair, weight = mean(effect × confidence). Opposing evidence may cancel. W[target, source] is divided by max(1, maximum absolute row sum). Dynamics: x[t+1] = tanh(gain × W × x[t] + input[t]); input is zero after pulse duration. Baseline is zero and model units are arbitrary. The gain is below one. This model does not predict real pharmacology or biological recovery.

## Reproducibility
Seed 42 fixes network layout. Results ZIP preserves parameters, selected evidence and software versions. requirements.txt contains compatible version ranges, not an exact lock; use pip freeze to record your deployed environment. Source code should be retained with each experiment.

Documentation:
https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
https://docs.streamlit.io/develop/api-reference/widgets/st.download_button
https://networkx.org/documentation/stable/reference/algorithms/simple_paths.html
