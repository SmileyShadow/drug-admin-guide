# drug_admin_app.py

import streamlit as st
import requests

# Title
st.title("Drug Administration Guide")

# Input field with dynamic suggestions via OpenFDA
query = st.text_input("Enter drug name (e.g., Metformin)")

suggestions = []
if query and query.strip():
    q = query.strip().lower()
    try:
        resp = requests.get(
            "https://api.fda.gov/drug/label.json",
            params={
                "search": f"openfda.brand_name:{q}* OR openfda.generic_name:{q}*",  
                "limit": 10
            }
        )
        data = resp.json()
        api_names = []
        for r in data.get("results", []):
            api = r.get("openfda", {})
            api_names += api.get("brand_name", [])
            api_names += api.get("generic_name", [])
        # Deduplicate
        suggestions = list(dict.fromkeys(api_names))
    except:
        suggestions = []

# Show suggestions dropdown
if suggestions:
    choice = st.selectbox("Suggestions (choose or type)", [""] + suggestions)
    if choice:
        query = choice

# Fetch and display instructions
if st.button("Get Instructions"):
    if not query or not query.strip():
        st.warning("Please enter or select a drug name.")
    else:
        with st.spinner("Fetching data..."):
            try:
                resp = requests.get(
                    "https://api.fda.gov/drug/label.json",
                    params={
                        "search": f"openfda.brand_name:{query} OR openfda.generic_name:{query}",
                        "limit": 1
                    }
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
                        for item in indications:
                            st.write("-", item)
                    else:
                        st.write("No data.")

                    st.subheader("Dosage & Administration")
                    if dosage:
                        for item in dosage:
                            st.write("-", item)
                    else:
                        st.write("No data.")

                    if interactions or precautions:
                        st.subheader("Interactions & Precautions")
                        if interactions:
                            st.write("**Interactions:**")
                            for item in interactions:
                                st.write("-", item)
                        if precautions:
                            st.write("**Precautions:**")
                            for item in precautions:
                                st.write("-", item)
            except Exception as e:
                st.error(f"Error fetching data: {e}")

# Running instructions:
# pip install streamlit requests
# streamlit run drug_admin_app.py
