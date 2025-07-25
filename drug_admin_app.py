# drug_admin_app.py

import streamlit as st
import requests
from urllib.parse import quote_plus

# --- Configuration ---
FDA_LABEL_URL = "https://api.fda.gov/drug/label.json"

# --- Caching ---
@st.cache_data(show_spinner=False)
def fetch_suggestions(query: str):
    """
    Fetch up to 10 brand or generic name suggestions matching the query.
    Uses proper OpenFDA search syntax with OR and URL encoding.
    """
    q = query.strip()
    if not q:
        return []
    # Build OpenFDA search expression
    expr = f'(openfda.brand_name:"{q}" OR openfda.generic_name:"{q}")'
    params = {"search": expr, "limit": 10}
    try:
        resp = requests.get(FDA_LABEL_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        api_names = []
        for r in data.get("results", []):
            of = r.get("openfda", {})
            api_names += of.get("brand_name", [])
            api_names += of.get("generic_name", [])
        # Deduplicate and return
        return list(dict.fromkeys(api_names))
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def fetch_instructions(query: str):
    """
    Fetch the first matching drug label entry and extract key fields.
    Returns a dict with lists: indications, dosage, interactions, precautions.
    """
    q = query.strip()
    if not q:
        return None
    expr = f'(openfda.brand_name:"{q}" OR openfda.generic_name:"{q}")'
    params = {"search": expr, "limit": 1}
    resp = requests.get(FDA_LABEL_URL, params=params, timeout=5)
    if resp.status_code != 200:
        return None
    data = resp.json()
    results = data.get("results", [])
    if not results:
        return None
    r = results[0]
    return {
        "indications": r.get("indications_and_usage", []),
        "dosage": r.get("dosage_and_administration", []),
        "interactions": r.get("drug_interactions", []),
        "precautions": r.get("precautions_and_warnings", [])
    }

# --- UI ---
st.set_page_config(page_title="Drug Administration Guide", layout="centered")
st.title("💊 Drug Administration Guide")

# Input & Suggestions
query = st.text_input("Enter drug name", value="")
suggestions = fetch_suggestions(query)
if suggestions:
    choice = st.selectbox("Suggestions (choose or continue typing)", [""] + suggestions)
    if choice:
        query = choice

# Fetch button
if st.button("Get Instructions"):
    if not query.strip():
        st.warning("Please enter or select a drug name.")
    else:
        with st.spinner("Fetching information..."):
            info = fetch_instructions(query)
        if info is None:
            st.error("No trusted information found. Please verify drug name or try another.")
        else:
            # Key summary
            st.header("Key Patient Instructions 📋")
            main_ind = info["indications"][0] if info["indications"] else "Not available."
            admin = info["dosage"][0] if info["dosage"] else "Not available."
            important = (
                info["interactions"][0] or info["precautions"][0]
                if info["interactions"] or info["precautions"]
                else "None noted."
            )
            st.markdown(f"**Main Indication:** {main_ind}")
            st.markdown(f"**Administration:** {admin}")
            st.markdown(f"**Important Instructions:** {important}")

            # Detailed sections
            st.subheader("Indications & Usage")
            if info["indications"]:
                for i in info["indications"]:
                    st.write(f"- {i}")
            else:
                st.write("No data.")

            st.subheader("Dosage & Administration")
            if info["dosage"]:
                for d in info["dosage"]:
                    st.write(f"- {d}")
            else:
                st.write("No data.")

            if info["interactions"] or info["precautions"]:
                st.subheader("Interactions & Precautions")
                if info["interactions"]:
                    st.write("**Interactions:**")
                    for x in info["interactions"]:
                        st.write(f"- {x}")
                if info["precautions"]:
                    st.write("**Precautions:**")
                    for p in info["precautions"]:
                        st.write(f"- {p}")

            # Disclaimer
            st.caption(
                "Data from FDA open API; please verify with official prescribing information before clinical use."
            )

# --- Instructions ---
# 1. pip install streamlit requests
# 2. streamlit run drug_admin_app.py
