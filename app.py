import streamlit as st
import pandas as pd

# Set page configuration for a professional look
st.set_page_config(page_title="Bare-Stem Valve Costing Tool", layout="wide")

st.title("Bare-Stem Valve Costing Calculator")
st.markdown("Select the valve specifications below to generate dynamic component costs.")

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    # Ensure this matches your exact GitHub file name
    catalogue = pd.read_excel("Component catalogue.xlsx")
    return catalogue

df_catalogue = load_data()

# --- 2. PRIMARY SELECTION CRITERIA ---
st.header("1. Valve Specification")
col1, col2, col3, col4 = st.columns(4)

with col1:
    valve_type = st.selectbox("Valve Type", ["Ball Valve", "Butterfly Valve"])

with col2:
    if valve_type == "Ball Valve":
        sub_type = st.selectbox("Design Type", ["Floating", "Trunnion Mounted"])
    else:
        sub_type = st.selectbox("Design Type", ["Concentric", "Double Offset", "Triple Offset"])

with col3:
    size = st.selectbox("Size", ['2"', '3"', '4"', '6"', '8"', '10"', '12"'])

with col4:
    pressure_class = st.selectbox("Pressure Class", ["150#", "300#", "600#", "900#", "1500#"])

st.markdown("---")

# --- 3. FILTERING THE DATABASE ---
try:
    filtered_df = df_catalogue[
        (df_catalogue['Size'] == size) & 
        (df_catalogue['Class'] == pressure_class)
    ]
except KeyError:
    st.warning("Please ensure your Excel file has columns named exactly 'Size' and 'Class'.")
    filtered_df = df_catalogue

# --- 4. COMPONENT MOC SELECTION ---
st.header(f"2. Component Selection for {size} {pressure_class} {sub_type} {valve_type}")
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Major Components")
    # Fetching unique materials from the filtered dataframe
    body_materials = filtered_df[filtered_df['Component'] == 'Body']['Material'].unique() if 'Component' in filtered_df.columns else []
    body_moc = st.selectbox("Body MOC", body_materials if len(body_materials) > 0 else ["No data"])
    
    trim_materials = filtered_df[filtered_df['Component'] == 'Trim']['Material'].unique() if 'Component' in filtered_df.columns else []
    trim_moc = st.selectbox("Trim MOC", trim_materials if len(trim_materials) > 0 else ["No data"])

with col_b:
    st.subheader("Hardware & Seals")
    bolting_materials = filtered_df[filtered_df['Component'] == 'Bolting']['Material'].unique() if 'Component' in filtered_df.columns else []
    bolting_moc = st.selectbox("Bolting", bolting_materials if len(bolting_materials) > 0 else ["No data"])
    
    seal_materials = filtered_df[filtered_df['Component'] == 'Seals']['Material'].unique() if 'Component' in filtered_df.columns else []
    seal_moc = st.selectbox("Soft Seals", seal_materials if len(seal_materials) > 0 else ["No data"])


# --- 5. COST CALCULATION ENGINE ---
st.markdown("---")
st.header("3. Cost Summary")

# A quick helper function to extract the cost from the dataframe based on the user's selection
def get_cost(component_name, material_name):
    try:
        cost_series = filtered_df[(filtered_df['Component'] == component_name) & (filtered_df['Material'] == material_name)]['Unit Cost (₹)']
        if not cost_series.empty:
            return float(cost_series.values[0])
        return 0.0
    except Exception:
        return 0.0

# Fetch costs for the selected items
body_cost = get_cost('Body', body_moc)
trim_cost = get_cost('Trim', trim_moc)
bolting_cost = get_cost('Bolting', bolting_moc)
seal_cost = get_cost('Seals', seal_moc)

# Calculate totals
total_component_cost = sum([body_cost, trim_cost, bolting_cost, seal_cost])

# Add the 4% conversion cost behind the scenes (multiply by 1.04)
final_barestem_cost = total_component_cost * 1.04

# Display the Final Cost cleanly using Streamlit's metric widget
st.metric(label="Barestem Valve Cost (₹)", value=f"₹ {final_barestem_cost:,.2f}")

# --- 6. BILL OF MATERIAL (Hidden in Expander) ---
# Create the dataframe for the BOM
bom_data = {
    "Component": ["Body", "Trim", "Bolting", "Soft Seals"],
    "Material Selected": [body_moc, trim_moc, bolting_moc, seal_moc],
    "Cost (₹)": [body_cost, trim_cost, bolting_cost, seal_cost]
}
df_bom = pd.DataFrame(bom_data)

# 'expanded=False' ensures it stays hidden until clicked, and resets when selections change
with st.expander("View Bill of Material (BOM)", expanded=False):
    st.dataframe(df_bom, use_container_width=True)
