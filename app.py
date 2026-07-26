import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Bare-Stem Valve Costing Tool", layout="wide")

st.title("Bare-Stem Valve Costing Calculator")
st.markdown("Select the valve specifications below to generate dynamic component costs.")

# --- 1. DATA LOADING ---
@st.cache_data
def load_data():
    catalogue = pd.read_excel("Component catalogue_2.xlsx")
    matrix = pd.read_excel("MOC Rules Matrix.xlsx")
    return catalogue, matrix

try:
    df_catalogue, df_matrix = load_data()
except Exception as e:
    st.error("Error loading files. Ensure both 'Component catalogue_2.xlsx' and 'MOC Rules Matrix.xlsx' are uploaded to GitHub.")
    st.stop()

# --- 2. PRIMARY SELECTION CRITERIA ---
st.header("1. Valve Specification")
col1, col2, col3, col4 = st.columns(4)

with col1:
    valve_types = df_catalogue['Valve Type'].dropna().unique().tolist()
    valve_type = st.selectbox("Valve Type", valve_types)

with col2:
    sub_types = df_catalogue[df_catalogue['Valve Type'] == valve_type]['Sub-Type'].dropna().unique().tolist()
    sub_type = st.selectbox("Sub-Type", sub_types)

with col3:
    sizes = df_catalogue[(df_catalogue['Valve Type'] == valve_type) & 
                         (df_catalogue['Sub-Type'] == sub_type)]['Size'].dropna().unique().tolist()
    size = st.selectbox("Size", sizes)

with col4:
    classes = df_catalogue[(df_catalogue['Valve Type'] == valve_type) & 
                           (df_catalogue['Sub-Type'] == sub_type) &
                           (df_catalogue['Size'] == size)]['Class'].dropna().unique().tolist()
    pressure_class = st.selectbox("Class", classes)

st.markdown("---")

# --- 3. FILTERING THE DATABASE ---
filtered_df = df_catalogue[
    (df_catalogue['Valve Type'] == valve_type) &
    (df_catalogue['Sub-Type'] == sub_type) &
    (df_catalogue['Size'] == size) & 
    (df_catalogue['Class'] == pressure_class)
]

# --- 4. COMPONENT SELECTION (Manual & Matrix Auto-Select) ---
st.header(f"2. Component Selection for {size} Class {pressure_class} {sub_type} {valve_type}")
components_in_valve = filtered_df['Component Name'].dropna().unique().tolist()
selected_mocs = {}

col_a, col_b = st.columns(2)

# Left Column: Body, Disc, Stem
with col_a:
    st.subheader("Major Components")
    
    # 1. Body Selection & Matrix Trigger
    if 'Body' in components_in_valve:
        body_mocs = filtered_df[filtered_df['Component Name'] == 'Body']['MOC'].dropna().unique().tolist()
        body_moc = st.selectbox("Body MOC", body_mocs)
        selected_mocs['Body'] = body_moc
    else:
        body_moc = None
        
    # Check Matrix Rules based on selected Body MOC
    auto_flange_moc = None
    auto_other_moc = None
    if body_moc and not df_matrix.empty:
        rule = df_matrix[df_matrix['Selected Body MOC'] == body_moc]
        if not rule.empty:
            auto_flange_moc = rule['Auto-Select Flange MOC'].values[0]
            auto_other_moc = rule["Auto-Select 'Other' MOC"].values[0]
            
    # 2. Disc
    if 'Disc' in components_in_valve:
        disc_mocs = filtered_df[filtered_df['Component Name'] == 'Disc']['MOC'].dropna().unique().tolist()
        disc_moc = st.selectbox("Disc MOC", disc_mocs)
        selected_mocs['Disc'] = disc_moc
        
    # 3. Stem
    if 'Stem' in components_in_valve:
        stem_mocs = filtered_df[filtered_df['Component Name'] == 'Stem']['MOC'].dropna().unique().tolist()
        stem_moc = st.selectbox("Stem MOC", stem_mocs)
        selected_mocs['Stem'] = stem_moc

# Right Column: Seat, Bolting, Other Bundles
with col_b:
    st.subheader("Seat & Hardware")
    
    # 4. Under Seat Selection
    seat_options = [c for c in ['Non Firesafe Seat', 'Firesafe Seat Ring'] if c in components_in_valve]
    if seat_options:
        seat_type = st.radio("Under Seat Type", seat_options)
        seat_mocs = filtered_df[filtered_df['Component Name'] == seat_type]['MOC'].dropna().unique().tolist()
        if seat_mocs:
            seat_moc = st.selectbox(f"{seat_type} MOC", seat_mocs)
            selected_mocs[seat_type] = seat_moc
            
    # 5. Bolting set
    if 'Bolting set' in components_in_valve:
        bolt_mocs = filtered_df[filtered_df['Component Name'] == 'Bolting set']['MOC'].dropna().unique().tolist()
        bolt_moc = st.selectbox("Bolting Set MOC", bolt_mocs)
        selected_mocs['Bolting set'] = bolt_moc
        
    # 6. Other Components Bundle (Matrix Auto-Selected Default)
    if 'Other Components Bundle' in components_in_valve:
        other_mocs = filtered_df[filtered_df['Component Name'] == 'Other Components Bundle']['MOC'].dropna().unique().tolist()
        
        # Set default dropdown index based on Matrix Rule
        default_idx = 0
        if auto_other_moc and auto_other_moc in other_mocs:
            default_idx = other_mocs.index(auto_other_moc)
            
        other_moc = st.selectbox("Other Components Bundle MOC", other_mocs, index=default_idx)
        selected_mocs['Other Components Bundle'] = other_moc


# --- BACKGROUND AUTO-ADDITIONS ---
# Automatically assign matrix 'Flange' MOC rules to background components
auto_flange_items = ['Gland Flange', 'Bottom Flange', 'Retainer Ring', 'Bracket']
for item in auto_flange_items:
    if item in components_in_valve:
        comp_mocs = filtered_df[filtered_df['Component Name'] == item]['MOC'].dropna().unique().tolist()
        
        # Apply matrix rule if available in catalogue, otherwise fallback to first available
        if auto_flange_moc and auto_flange_moc in comp_mocs:
            selected_mocs[item] = auto_flange_moc
        elif comp_mocs:
            selected_mocs[item] = comp_mocs[0] 
        else:
            selected_mocs[item] = "No Data"

st.markdown("---")

# --- 5. COST CALCULATION ENGINE ---
st.header("3. Cost Summary")
component_costs = {}

for comp, moc in selected_mocs.items():
    try:
        cost_series = filtered_df[(filtered_df['Component Name'] == comp) & (filtered_df['MOC'] == moc)]['Unit Cost (₹)']
        component_costs[comp] = float(cost_series.values[0]) if not cost_series.empty else 0.0
    except:
        component_costs[comp] = 0.0

# Summing logic & hiding the 4% conversion markup
total_component_cost = sum(component_costs.values())
final_barestem_cost = total_component_cost * 1.04 

st.metric(label="Barestem Valve Cost (₹)", value=f"₹ {final_barestem_cost:,.2f}")

# --- 6. BILL OF MATERIAL (Hidden in Expander) ---
if selected_mocs:
    df_bom = pd.DataFrame({
        "Component Name": list(selected_mocs.keys()),
        "MOC Selected": list(selected_mocs.values()),
        "Unit Cost (₹)": list(component_costs.values())
    })
    
    with st.expander("View Bill of Material (BOM)", expanded=False):
        st.dataframe(df_bom, use_container_width=True)
