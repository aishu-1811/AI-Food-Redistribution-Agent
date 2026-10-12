import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from foodrescue import init_db, add_donation, list_donations, list_ngos, match_donations, update_status, impact_summary, seed_demo_data

st.set_page_config(page_title="FoodRescue AI", page_icon="🥗", layout="wide")
init_db()

st.title("🥗 FoodRescue AI")
st.caption("AI-assisted food redistribution • SDG 2: Zero Hunger")
st.info("Demo project: matching recommendations use food type, quantity, urgency, location proximity (simple distance), and NGO capacity. Use demo data or add your own records.")

with st.sidebar:
    st.header("Workspace")
    page = st.radio("Go to", ["Dashboard", "Add food donation", "Redistribution matches", "NGO directory", "About"])
    if st.button("Load demo data"):
        seed_demo_data()
        st.success("Demo records added. Open Dashboard or Redistribution matches.")

if page == "Dashboard":
    donations = list_donations()
    metrics = impact_summary()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Donations recorded", metrics["donations"])
    c2.metric("Food available", f'{metrics["available_kg"]:.1f} kg')
    c3.metric("Food redistributed", f'{metrics["redistributed_kg"]:.1f} kg')
    c4.metric("Open requests / offers", metrics["open_items"])
    st.subheader("Recent food offers")
    if donations:
        df = pd.DataFrame(donations)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download donations CSV", df.to_csv(index=False).encode("utf-8"), "food_donations.csv", "text/csv")
    else:
        st.write("No donations yet. Add a donation or click **Load demo data** in the sidebar.")
    st.subheader("How the agent prioritizes")
    st.markdown("- **Urgency:** items nearing expiry are ranked higher.\n- **Suitability:** food category is compared with NGO needs.\n- **Capacity:** NGO capacity is considered before recommending a match.\n- **Distance:** a simple coordinate-based distance estimate helps rank nearby partners.")

elif page == "Add food donation":
    st.subheader("Register surplus food")
    with st.form("donation_form", clear_on_submit=True):
        a,b = st.columns(2)
        donor = a.text_input("Donor / business name", placeholder="e.g., Sunrise Bakery")
        food = b.selectbox("Food category", ["Cooked meals", "Bakery", "Vegetables", "Fruits", "Dairy", "Packaged food", "Grains", "Other"])
        c,d = st.columns(2)
        quantity = c.number_input("Quantity (kg)", min_value=0.1, max_value=10000.0, value=10.0, step=0.5)
        expiry = d.date_input("Use-by / expiry date", value=date.today() + timedelta(days=1), min_value=date.today())
        e,f = st.columns(2)
        city = e.text_input("City / area", value="Warangal")
        lat = f.number_input("Latitude (optional)", value=17.9689, format="%.5f")
        g,h = st.columns(2)
        lon = g.number_input("Longitude (optional)", value=79.5941, format="%.5f")
        notes = h.text_input("Notes / handling requirements", placeholder="Keep refrigerated, contains allergens...")
        submitted = st.form_submit_button("Save donation")
        if submitted:
            if not donor.strip():
                st.error("Please enter the donor name.")
            else:
                add_donation(donor.strip(), food, float(quantity), expiry.isoformat(), city.strip(), float(lat), float(lon), notes.strip())
                st.success("Donation saved. Visit Redistribution matches to find suitable NGOs.")

elif page == "Redistribution matches":
    st.subheader("Recommended redistribution matches")
    donations = list_donations(status="Available")
    if not donations:
        st.warning("No available donations found. Add a donation or load demo data.")
    else:
        selected = st.selectbox("Choose a donation", donations, format_func=lambda x: f'{x["id"]} · {x["food_type"]} · {x["quantity_kg"]} kg · expires {x["expiry_date"]} · {x["donor"]}')
        matches = match_donations(selected)
        if not matches:
            st.warning("No NGO matches found. Add NGOs in the NGO directory or load demo data.")
        else:
            st.markdown("Matches are ranked by a transparent demo score; confirm food safety, transport, and capacity with the NGO before handoff.")
            for rank, m in enumerate(matches, 1):
                with st.container(border=True):
                    left,right = st.columns([4,1])
                    left.markdown(f"**#{rank} {m['name']}** · {m['city']}")
                    left.write(f"Needs: {m['needs']} · Capacity: {m['capacity_kg']} kg · Approx. distance: {m['distance_km']:.1f} km")
                    left.write(f"**Recommendation score:** {m['score']}/100 — {m['reason']}")
                    if right.button("Mark redistributed", key=f"done_{selected['id']}_{m['id']}"):
                        update_status(selected["id"], "Redistributed")
                        st.success("Donation marked as redistributed.")
                        st.rerun()

elif page == "NGO directory":
    st.subheader("Food rescue partner directory")
    ngos = list_ngos()
    if ngos:
        st.dataframe(pd.DataFrame(ngos), use_container_width=True, hide_index=True)
    else:
        st.write("No NGO partners yet. Load demo data to populate sample partners.")
    st.markdown("### Add an NGO")
    with st.form("ngo_form", clear_on_submit=True):
        name = st.text_input("NGO / community kitchen name")
        needs = st.multiselect("Food categories accepted", ["Cooked meals", "Bakery", "Vegetables", "Fruits", "Dairy", "Packaged food", "Grains", "Other"])
        capacity = st.number_input("Available capacity (kg)", min_value=1.0, max_value=100000.0, value=50.0)
        city = st.text_input("City / area", value="Warangal")
        lat = st.number_input("Latitude", value=17.9689, format="%.5f", key="ngo_lat")
        lon = st.number_input("Longitude", value=79.5941, format="%.5f", key="ngo_lon")
        contact = st.text_input("Contact information (optional)")
        if st.form_submit_button("Add NGO"):
            if not name.strip() or not needs:
                st.error("Enter an NGO name and select at least one food category.")
            else:
                from foodrescue import add_ngo
                add_ngo(name.strip(), ", ".join(needs), float(capacity), city.strip(), float(lat), float(lon), contact.strip())
                st.success("NGO added.")
                st.rerun()

else:
    st.subheader("About FoodRescue AI")
    st.markdown("""
**Purpose:** reduce avoidable food waste by connecting surplus-food donors with food banks, NGOs, and community kitchens.

**Included in this prototype**
- Streamlit web dashboard
- Local SQLite database for donations and NGO partners
- Expiry-aware, needs-aware matching recommendations
- Demo records for testing
- CSV export of donation records

**Important limitations**
- The matching engine is a transparent heuristic, not a trained predictive model.
- Distance is an approximate straight-line estimate using entered coordinates; no live routing is used.
- This prototype does not verify food safety, contact NGOs, or arrange collection automatically.
- Use only safe, legally redistributable food and confirm cold-chain/handling requirements with recipients.
""")
