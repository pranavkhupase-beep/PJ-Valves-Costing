import streamlit as st
import pandas as pd

st.set_page_config(page_title="PJ Valves - Costing Tool", layout="wide")

st.title("Internal Pricing Matrix")
st.subheader("Butterfly - Double Offset - 4\" 150#")

# Load data securely
@st.cache_data
def load_data():
    cat = pd.read_excel("Component catalogue.xlsx")
    matrix = pd.read_excel("MOC Rules Matrix.xlsx")
    return cat, matrix

try:
    cat_df, matrix_df = load_data()
except Exception as e:
    st.error("Error loading Excel files. Ensure they are uploaded to GitHub correctly.")
    st.stop()

# Extract dropdown options from your database
bodies = cat_df[cat_df["Component Name"] == "Body"]["MOC"].unique()
discs = cat_df[cat_df["Component Name"] == "Disc"]["MOC"].unique()
stems = cat_df[cat_df["Component Name"] == "Stem"]["MOC"].unique()
bolts = cat_df[cat_df["Component Name"] == "Bolting Set"]["MOC"].unique()
seats_df = cat_df[cat_df["Component Name"].str.contains("seat", case=False, na=False)]
seat_options = (seats_df["Component Name"].str.strip() + " | " + seats_df["MOC"]).unique()

# Front-End UI
col1, col2 = st.columns(2)
with col1:
    body_moc = st.selectbox("1. Select Body MOC", bodies, help="Auto-locks Flanges & Other Components")
    disc_moc = st.selectbox("2. Select Disc MOC", discs, help="Auto-locks Retainer Ring")
    stem_moc = st.selectbox("3. Select Stem MOC", stems)
with col2:
    seat_selection = st.selectbox("4. Select Seat Option", seat_options)
    bolting_moc = st.selectbox("5. Select Bolting MOC", bolts)

st.divider()
st.subheader("Bill of Materials (BOM)")

bom = []

def add_item(name, moc, cost):
    bom.append({"Component": name, "MOC": moc, "Unit Cost (₹)": cost})

# Logic Execution
# 1. Body and Dependencies
body_cost = cat_df[(cat_df["Component Name"] == "Body") & (cat_df["MOC"] == body_moc)]["Unit Cost (₹)"].values[0]
add_item("Body", body_moc, body_cost)

rule = matrix_df[matrix_df["Selected Body MOC"] == body_moc].iloc[0]
flange_moc = rule["Auto-Select Flange MOC"]
other_moc = rule["Auto-Select 'Other' MOC"]

for comp in ["Gland Flange", "Bottom Flange"]:
    cost = cat_df[(cat_df["Component Name"] == comp) & (cat_df["MOC"] == flange_moc)]["Unit Cost (₹)"].values[0]
    add_item(comp, flange_moc, cost)

other_cost = cat_df[(cat_df["Component Name"] == "Other Components Bundle*") & (cat_df["MOC"] == other_moc)]["Unit Cost (₹)"].values[0]
add_item("Other Components Bundle", other_moc, other_cost)

# 2. Disc and Dependencies
disc_cost = cat_df[(cat_df["Component Name"] == "Disc") & (cat_df["MOC"] == disc_moc)]["Unit Cost (₹)"].values[0]
add_item("Disc", disc_moc, disc_cost)

ret_cost = cat_df[(cat_df["Component Name"] == "Retainer Ring") & (cat_df["MOC"] == disc_moc)]["Unit Cost (₹)"].values[0]
add_item("Retainer Ring", disc_moc, ret_cost)

# 3. Independent Components
stem_cost = cat_df[(cat_df["Component Name"] == "Stem") & (cat_df["MOC"] == stem_moc)]["Unit Cost (₹)"].values[0]
add_item("Stem", stem_moc, stem_cost)

bolt_cost = cat_df[(cat_df["Component Name"] == "Bolting Set") & (cat_df["MOC"] == bolting_moc)]["Unit Cost (₹)"].values[0]
add_item("Bolting Set", bolting_moc, bolt_cost)

seat_name, seat_moc = [s.strip() for s in seat_selection.split("|")]
seat_cost = cat_df[(cat_df["Component Name"].str.strip() == seat_name) & (cat_df["MOC"] == seat_moc)]["Unit Cost (₹)"].values[0]
add_item(seat_name, seat_moc, seat_cost)

# Bracket
bracket_cost = cat_df[cat_df["Component Name"] == "Bracket"]["Unit Cost (₹)"].values[0]
add_item("Bracket", "CF8M", bracket_cost)

# Display Data
bom_df = pd.DataFrame(bom)
st.dataframe(bom_df, use_container_width=True, hide_index=True)

# Final Math
total_bare = bom_df["Unit Cost (₹)"].sum()
conversion = total_bare * 0.04
final_cost = total_bare * 1.04

# Dashboard Metrics
col3, col4, col5 = st.columns(3)
col3.metric("Total Bare-Stem Cost", f"₹ {total_bare:,.2f}")
col4.metric("Conversion Cost (4%)", f"₹ {conversion:,.2f}")
col5.metric("Final Calculated Cost", f"₹ {final_cost:,.2f}")
