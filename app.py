import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Bare-Stem Valve Costing Tool", layout="wide")

st.title("Bare-Stem Valve Costing Calculator")
st.markdown("Select the valve specifications below to generate dynamic component costs.")

# --- 1. DATA LOADING ---
@st.cache_data
def load_catalogue():
    return pd.read_excel("Component catalogue.xlsx")

@st.cache_data
def load_matrix(valve_type):
    try:
        # Dynamically load the sheet named "Ball" or "Butterfly"
        return pd.read_excel("MOC Rules Matrix.xlsx", sheet_name=valve_type)
    except Exception:
        # Fallback empty dataframe if the sheet isn't created yet
        return pd.DataFrame(columns=['Selected Body MOC', 'Auto-Select Flange MOC', "Auto-Select 'Other' MOC"])

try:
    df_cat = load_catalogue()
except Exception as e:
    st.error("Error loading 'Component catalogue.xlsx'. Please ensure it is uploaded.")
    st.stop()

# Failsafe: Create a dummy 'Bore' column if it hasn't been added to the Excel yet
if 'Bore' not in df_cat.columns:
    df_cat['Bore'] = "Full Bore"

# --- 2. PRIMARY SELECTION CRITERIA ---
st.header("1. Valve Specification")

# Bifurcate Layout based on Valve Type
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    valve_type = st.selectbox("Valve Type", ["Butterfly", "Ball"])

# Load matrix for the selected valve type
df_matrix = load_matrix(valve_type)

with col2:
    if valve_type == "Butterfly":
        sub_type_options = ["Concentric", "Eccentric", "Double Offset", "Triple Offset"]
    else:
        sub_type_options = ["Trunnion", "Floating"]
    sub_type = st.selectbox("Sub-Type", sub_type_options)

with col3:
    # Filter sizes based on catalogue
    available_sizes = df_cat[(df_cat['Valve Type'] == valve_type) & 
                             (df_cat['Sub-Type'] == sub_type)]['Size'].dropna().unique().tolist()
    size = st.selectbox("Size", available_sizes if available_sizes else ["No Data"])

with col4:
    # Filter classes based on catalogue
    available_classes = df_cat[(df_cat['Valve Type'] == valve_type) & 
                               (df_cat['Sub-Type'] == sub_type) &
                               (df_cat['Size'] == size)]['Class'].dropna().unique().tolist()
    pressure_class = st.selectbox("Class", available_classes if available_classes else ["No Data"])

with col5:
    if valve_type == "Ball":
        bore = st.selectbox("Bore", ["Full Bore", "Reduced Bore"])
    else:
        bore = None

st.markdown("---")

# --- 3. FILTERING THE DATABASE ---
if valve_type == "Ball":
    filtered_df = df_cat[
        (df_cat['Valve Type'] == valve_type) &
        (df_cat['Sub-Type'] == sub_type) &
        (df_cat['Size'] == size) & 
        (df_cat['Class'] == pressure_class) &
        (df_cat['Bore'] == bore)
    ]
else:
    filtered_df = df_cat[
        (df_cat['Valve Type'] == valve_type) &
        (df_cat['Sub-Type'] == sub_type) &
        (df_cat['Size'] == size) & 
        (df_cat['Class'] == pressure_class)
    ]

# --- 4. COMPONENT SELECTION ---
st.header(f"2. Component Selection")
selected_mocs = {}

col_a, col_b = st.columns(2)

# ---- LEFT COLUMN: Body & Closure ----
with col_a:
    st.subheader("Major Components")
    
    # 1. Body Type & MOC
    if valve_type == "Ball":
        body_type_ui = st.selectbox("Body Type", ["Casting", "Forging"])
        body_comp = "Casting Body" if body_type_ui == "Casting" else "Forged Body"
    else:
        # UPDATED LINE: Exact match for the catalogue capitalization
        body_type_ui = st.selectbox("Body Type", ["DF Body", "Lug Body", "Wafer Body"])
        body_comp = body_type_ui
        
    body_mocs = filtered_df[filtered_df['Component Name'] == body_comp]['MOC'].dropna().unique().tolist()
    if body_mocs:
        body_moc = st.selectbox("Body MOC", body_mocs)
        selected_mocs[body_comp] = body_moc
    else:
        body_moc = None
        st.warning(f"No MOC data found for {body_comp}")

    # Matrix Rules check based on Body MOC
    auto_flange_moc = None
    auto_other_moc = None
    if body_moc and not df_matrix.empty:
        rule = df_matrix[df_matrix['Selected Body MOC'] == body_moc]
        if not rule.empty:
            auto_flange_moc = rule['Auto-Select Flange MOC'].values[0]
            auto_other_moc = rule["Auto-Select 'Other' MOC"].values[0]

    # 2. Closure Member (Ball or Disc)
    closure_comp = "Ball" if valve_type == "Ball" else "Disc"
    closure_mocs = filtered_df[filtered_df['Component Name'] == closure_comp]['MOC'].dropna().unique().tolist()
    if closure_mocs:
        closure_moc = st.selectbox(f"{closure_comp} MOC", closure_mocs)
        selected_mocs[closure_comp] = closure_moc

    # 3. Stem
    stem_mocs = filtered_df[filtered_df['Component Name'] == 'Stem']['MOC'].dropna().unique().tolist()
    if stem_mocs:
        stem_moc = st.selectbox("Stem MOC", stem_mocs)
        selected_mocs['Stem'] = stem_moc


# ---- RIGHT COLUMN: Seats & Hardware ----
with col_b:
    st.subheader("Seat & Hardware")
    
    # 4. Seat Logic
    if valve_type == "Butterfly":
        seat_type = st.radio("Under Seat Type", ["Non Firesafe Seat", "Firesafe Seat Ring"])
        seat_mocs = filtered_df[filtered_df['Component Name'] == seat_type]['MOC'].dropna().unique().tolist()
        if seat_mocs:
            seat_moc = st.selectbox(f"{seat_type} MOC", seat_mocs)
            selected_mocs[seat_type] = seat_moc
            
    elif valve_type == "Ball":
        seat_type = st.radio("Seat Type", ["Soft seat", "Metal Seat"])
        seat_mocs = filtered_df[filtered_df['Component Name'] == seat_type]['MOC'].dropna().unique().tolist()
        if seat_mocs:
            seat_moc = st.selectbox(f"{seat_type} MOC", seat_mocs)
            selected_mocs[seat_type] = seat_moc
            
        # Seat Ring (Appears for all Ball valves)
        seat_ring_mocs = filtered_df[filtered_df['Component Name'] == 'Seat ring']['MOC'].dropna().unique().tolist()
        if seat_ring_mocs:
            seat_ring_moc = st.selectbox("Seat Ring MOC", seat_ring_mocs)
            selected_mocs['Seat ring'] = seat_ring_moc
            
        # Seat Insert (Appears ONLY if Soft seat is selected)
        if seat_type == "Soft seat":
            insert_mocs = filtered_df[filtered_df['Component Name'] == 'Seat insert']['MOC'].dropna().unique().tolist()
            if insert_mocs:
                insert_moc = st.selectbox("Seat Insert MOC", insert_mocs)
                selected_mocs['Seat insert'] = insert_moc

    # 5. Bolting set
    bolt_mocs = filtered_df[filtered_df['Component Name'] == 'Bolting set']['MOC'].dropna().unique().tolist()
    if bolt_mocs:
        bolt_moc = st.selectbox("Bolting Set MOC", bolt_mocs)
        selected_mocs['Bolting set'] = bolt_moc
        
    # 6. Other Components Bundle (Matrix Auto-Selected Default)
    other_mocs = filtered_df[filtered_df['Component Name'] == 'Other Components Bundle']['MOC'].dropna().unique().tolist()
    if other_mocs:
        default_idx = 0
        if auto_other_moc and auto_other_moc in other_mocs:
            default_idx = other_mocs.index(auto_other_moc)
        other_moc = st.selectbox("Other Components Bundle MOC", other_mocs, index=default_idx)
        selected_mocs['Other Components Bundle'] = other_moc


# --- BACKGROUND AUTO-ADDITIONS ---
auto_flange_items = ['Gland Flange', 'Bottom Flange', 'Retainer Ring', 'Bracket']
for item in auto_flange_items:
    comp_mocs = filtered_df[filtered_df['Component Name'] == item]['MOC'].dropna().unique().tolist()
    if comp_mocs:
        if auto_flange_moc and auto_flange_moc in comp_mocs:
            selected_mocs[item] = auto_flange_moc
        else:
            selected_mocs[item] = comp_mocs[0]

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
with col5:
    if valve_type == "Ball":
        bore = st.selectbox("Bore", ["Full Bore", "Reduced Bore"])
    else:
        bore = None

st.markdown("---")

# --- 3. FILTERING THE DATABASE ---
if valve_type == "Ball":
    filtered_df = df_cat[
        (df_cat['Valve Type'] == valve_type) &
        (df_cat['Sub-Type'] == sub_type) &
        (df_cat['Size'] == size) & 
        (df_cat['Class'] == pressure_class) &
        (df_cat['Bore'] == bore)
    ]
else:
    filtered_df = df_cat[
        (df_cat['Valve Type'] == valve_type) &
        (df_cat['Sub-Type'] == sub_type) &
        (df_cat['Size'] == size) & 
        (df_cat['Class'] == pressure_class)
    ]

# --- 4. COMPONENT SELECTION ---
st.header(f"2. Component Selection")
selected_mocs = {}

col_a, col_b = st.columns(2)

# ---- LEFT COLUMN: Body & Closure ----
with col_a:
    st.subheader("Major Components")
    
    # 1. Body Type & MOC
    if valve_type == "Ball":
        body_type_ui = st.selectbox("Body Type", ["Casting", "Forging"])
        body_comp = "Casting Body" if body_type_ui == "Casting" else "Forged Body"
    else:
        body_type_ui = st.selectbox("Body Type", ["DF body", "Lug body", "wafer Body"])
        body_comp = body_type_ui
        
    body_mocs = filtered_df[filtered_df['Component Name'] == body_comp]['MOC'].dropna().unique().tolist()
    if body_mocs:
        body_moc = st.selectbox("Body MOC", body_mocs)
        selected_mocs[body_comp] = body_moc
    else:
        body_moc = None
        st.warning(f"No MOC data found for {body_comp}")

    # Matrix Rules check based on Body MOC
    auto_flange_moc = None
    auto_other_moc = None
    if body_moc and not df_matrix.empty:
        rule = df_matrix[df_matrix['Selected Body MOC'] == body_moc]
        if not rule.empty:
            auto_flange_moc = rule['Auto-Select Flange MOC'].values[0]
            auto_other_moc = rule["Auto-Select 'Other' MOC"].values[0]

    # 2. Closure Member (Ball or Disc)
    closure_comp = "Ball" if valve_type == "Ball" else "Disc"
    closure_mocs = filtered_df[filtered_df['Component Name'] == closure_comp]['MOC'].dropna().unique().tolist()
    if closure_mocs:
        closure_moc = st.selectbox(f"{closure_comp} MOC", closure_mocs)
        selected_mocs[closure_comp] = closure_moc

    # 3. Stem
    stem_mocs = filtered_df[filtered_df['Component Name'] == 'Stem']['MOC'].dropna().unique().tolist()
    if stem_mocs:
        stem_moc = st.selectbox("Stem MOC", stem_mocs)
        selected_mocs['Stem'] = stem_moc


# ---- RIGHT COLUMN: Seats & Hardware ----
with col_b:
    st.subheader("Seat & Hardware")
    
    # 4. Seat Logic
    if valve_type == "Butterfly":
        seat_type = st.radio("Under Seat Type", ["Non Firesafe Seat", "Firesafe Seat Ring"])
        seat_mocs = filtered_df[filtered_df['Component Name'] == seat_type]['MOC'].dropna().unique().tolist()
        if seat_mocs:
            seat_moc = st.selectbox(f"{seat_type} MOC", seat_mocs)
            selected_mocs[seat_type] = seat_moc
            
    elif valve_type == "Ball":
        seat_type = st.radio("Seat Type", ["Soft seat", "Metal Seat"])
        seat_mocs = filtered_df[filtered_df['Component Name'] == seat_type]['MOC'].dropna().unique().tolist()
        if seat_mocs:
            seat_moc = st.selectbox(f"{seat_type} MOC", seat_mocs)
            selected_mocs[seat_type] = seat_moc
            
        # Seat Ring (Appears for all Ball valves)
        seat_ring_mocs = filtered_df[filtered_df['Component Name'] == 'Seat ring']['MOC'].dropna().unique().tolist()
        if seat_ring_mocs:
            seat_ring_moc = st.selectbox("Seat Ring MOC", seat_ring_mocs)
            selected_mocs['Seat ring'] = seat_ring_moc
            
        # Seat Insert (Appears ONLY if Soft seat is selected)
        if seat_type == "Soft seat":
            insert_mocs = filtered_df[filtered_df['Component Name'] == 'Seat insert']['MOC'].dropna().unique().tolist()
            if insert_mocs:
                insert_moc = st.selectbox("Seat Insert MOC", insert_mocs)
                selected_mocs['Seat insert'] = insert_moc

    # 5. Bolting set
    bolt_mocs = filtered_df[filtered_df['Component Name'] == 'Bolting set']['MOC'].dropna().unique().tolist()
    if bolt_mocs:
        bolt_moc = st.selectbox("Bolting Set MOC", bolt_mocs)
        selected_mocs['Bolting set'] = bolt_moc
        
    # 6. Other Components Bundle (Matrix Auto-Selected Default)
    other_mocs = filtered_df[filtered_df['Component Name'] == 'Other Components Bundle']['MOC'].dropna().unique().tolist()
    if other_mocs:
        default_idx = 0
        if auto_other_moc and auto_other_moc in other_mocs:
            default_idx = other_mocs.index(auto_other_moc)
        other_moc = st.selectbox("Other Components Bundle MOC", other_mocs, index=default_idx)
        selected_mocs['Other Components Bundle'] = other_moc


# --- BACKGROUND AUTO-ADDITIONS ---
auto_flange_items = ['Gland Flange', 'Bottom Flange', 'Retainer Ring', 'Bracket']
for item in auto_flange_items:
    comp_mocs = filtered_df[filtered_df['Component Name'] == item]['MOC'].dropna().unique().tolist()
    if comp_mocs:
        if auto_flange_moc and auto_flange_moc in comp_mocs:
            selected_mocs[item] = auto_flange_moc
        else:
            selected_mocs[item] = comp_mocs[0]

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
