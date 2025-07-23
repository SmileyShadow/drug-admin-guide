# drug_admin_app.py

import streamlit as st
import requests
import json

# Cache data loading for performance
@st.cache_data

def load_saudi_drugs():
    """
    Load the list of generic/brand names available in Saudi Arabia from a local JSON file.
    Create `saudi_drugs.json` in the same folder with a JSON array of strings.
    """
    with open('saudi_drugs.json', 'r', encoding='utf-8') as f:
        return json.load(f)

saudi_drugs = load_saudi_drugs()

# App title
st.title("Drug Administration Guide")

# Input field
query = st.text_input("Enter drug name", value="")

# Build suggestions list
suggestions = []
if query:
    q = query.strip().lower()
    # Local suggestions from Saudi list
    suggestions = [name for name in saudi_drugs if name.lower().startswith(q)]
    # API-based suggestions
    try:
        resp = requests.get(
            "https://api.fda.gov/drug/label.json",
            params={"search": f"openfda.brand_name:{q}*", "limit": 10}
        )
        data = resp.json()
        api_names = []
        for r in data.get("results", []):
            api_names += r.get("openfda", {}).get("brand_name", [])
            api_names += r.get("openfda", {}).get("generic_name", [])
        # Unique and combine
        suggestions = list(dict.fromkeys(suggestions + api_names))
    except:
        # Fallback to local only
        pass

# Show suggestions dropdown
if suggestions:
    choice = st.selectbox("Suggestions (choose or continue typing)", [""] + suggestions)
    if choice:
        query = choice

# Fetch and display instructions
if st.button("Get Instructions"):
    if not query:
        st.warning("Please enter a drug name or select from suggestions.")
    else:
        try:
            with st.spinner("Fetching data..."):
                resp = requests.get(
                    "https://api.fda.gov/drug/label.json",
                    params={"search": f"openfda.brand_name:{query}", "limit": 1}
                )
                data = resp.json()

            results = data.get("results", [])
            if not results:
                st.error("No instructions found for this medication.")
            else:
                r = results[0]
                dosage = r.get("dosage_and_administration", [])
                indications = r.get("indications_and_usage", [])
                interactions = r.get("drug_interactions", [])
                precautions = r.get("precautions_and_warnings", [])

                # Key summary
                st.header("Key Patient Instructions")
                st.markdown(f"**Main Indication:** {indications[0] if indications else 'Not available.'}")
                st.markdown(f"**Administration:** {dosage[0] if dosage else 'Not available.'}")
                important = interactions[0] if interactions else (precautions[0] if precautions else 'None noted.')
                st.markdown(f"**Important Instructions:** {important}")

                # Detailed sections
                st.subheader("Indications & Usage")
                if indications:
                    for i in indications:
                        st.write("-", i)
                else:
                    st.write("No data.")

                st.subheader("Dosage & Administration")
                if dosage:
                    for d in dosage:
                        st.write("-", d)
                else:
                    st.write("No data.")

                if interactions or precautions:
                    st.subheader("Interactions & Precautions")
                    if interactions:
                        st.write("**Interactions:**")
                        for inter in interactions:
                            st.write("-", inter)
                    if precautions:
                        st.write("**Precautions:**")
                        for p in precautions:
                            st.write("-", p)
        except Exception as e:
            st.error(f"Error fetching data: {e}")

# Instructions for running:
# 1. pip install streamlit requests
# 2. Create `saudi_drugs.json` with your local drug names.
# 3. streamlit run drug_admin_app.py
# All tools and APIs used are free and open-source.
