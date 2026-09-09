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
        return pd.read_excel("MOC Rules Matrix.xlsx", sheet_name=valve_type)
    except Exception:
        return pd.DataFrame(columns=['Selected Body MOC', 'Auto-Select Flange MOC', "Auto-Select 'Other' MOC"])

try:
    df_cat = load_catalogue()
except Exception as e:
    st.error("Error loading 'Component catalogue.xlsx'. Please ensure it is uploaded.")
    st.stop()

if 'Bore' not in df_cat.columns:
    df_cat['Bore'] = "Full Bore"

# --- 2. PRIMARY SELECTION CRITERIA ---
st.header("1. Valve Specification")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    valve_type = st.selectbox("Valve Type", ["Butterfly", "Ball"])

df_matrix = load_matrix(valve_type)

with col2:
    if valve_type == "Butterfly":
        sub_type_options = ["Concentric", "Eccentric", "Double Offset", "Triple Offset"]
    else:
        sub_type_options = ["Trunnion", "Floating"]
    sub_type = st.selectbox("Sub-Type", sub_type_options)

with col3:
    available_classes = df_cat[(df_cat['Valve Type'] == valve_type) & 
                               (df_cat['Sub-Type'] == sub_type)]['Class'].dropna().unique().tolist()
    pressure_class = st.selectbox("Class", available_classes if available_classes else ["No Data"])

with col4:
    available_sizes = df_cat[(df_cat['Valve Type'] == valve_type) & 
                             (df_cat['Sub-Type'] == sub_type) &
                             (df_cat['Class'] == pressure_class)]['Size'].dropna().unique().tolist()
    default_size = [available_sizes[0]] if available_sizes else []
    sizes = st.multiselect("Size(s)", available_sizes, default=default_size)

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
        (df_cat['Size'].isin(sizes)) & 
        (df_cat['Class'] == pressure_class) &
        (df_cat['Bore'] == bore)
    ]
else:
    filtered_df = df_cat[
        (df_cat['Valve Type'] == valve_type) &
        (df_cat['Sub-Type'] == sub_type) &
        (df_cat['Size'].isin(sizes)) & 
        (df_cat['Class'] == pressure_class)
    ]

# --- 4. COMPONENT SELECTION ---
size_label = ", ".join(sizes) if sizes else "No Size Selected"
st.header(f"2. Component Selection for {size_label}")
selected_mocs = {}

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Major Components")
    
    if valve_type == "Ball":
        body_type_ui = st.selectbox("Body Type", ["Casting", "Forging"])
        body_comp = "Casting Body" if body_type_ui == "Casting" else "Forged Body"
    else:
        body_type_ui = st.selectbox("Body Type", ["DF Body", "Lug Body", "Wafer Body"])
        body_comp = body_type_ui
        
    body_mocs = filtered_df[filtered_df['Component Name'] == body_comp]['MOC'].dropna().unique().tolist()
    if body_mocs:
        body_moc = st.selectbox("Body MOC", body_mocs)
        selected_mocs[body_comp] = body_moc
    else:
        body_moc = None
        st.warning(f"No MOC data found for {body_comp}")

    auto_flange_moc = None
    auto_other_moc = None
    if body_moc and not df_matrix.empty:
        rule = df_matrix[df_matrix['Selected Body MOC'] == body_moc]
        if not rule.empty:
            auto_flange_moc = rule['Auto-Select Flange MOC'].values[0]
            auto_other_moc = rule["Auto-Select 'Other' MOC"].values[0]

    closure_comp = "Ball" if valve_type == "Ball" else "Disc"
    closure_mocs = filtered_df[filtered_df['Component Name'] == closure_comp]['MOC'].dropna().unique().tolist()
    if closure_mocs:
        closure_moc = st.selectbox(f"{closure_comp} MOC", closure_mocs)
        selected_mocs[closure_comp] = closure_moc

    stem_mocs = filtered_df[filtered_df['Component Name'] == 'Stem']['MOC'].dropna().unique().tolist()
    if stem_mocs:
        stem_moc = st.selectbox("Stem MOC", stem_mocs)
        selected_mocs['Stem'] = stem_moc

with col_b:
    st.subheader("Seat & Hardware")
    
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
            
        seat_ring_mocs = filtered_df[filtered_df['Component Name'] == 'Seat ring']['MOC'].dropna().unique().tolist()
        if seat_ring_mocs:
            seat_ring_moc = st.selectbox("Seat Ring MOC", seat_ring_mocs)
            selected_mocs['Seat ring'] = seat_ring_moc
            
        if seat_type == "Soft seat":
            insert_mocs = filtered_df[filtered_df['Component Name'] == 'Seat insert']['MOC'].dropna().unique().tolist()
            if insert_mocs:
                insert_moc = st.selectbox("Seat Insert MOC", insert_mocs)
                selected_mocs['Seat insert'] = insert_moc

    bolt_mocs = filtered_df[filtered_df['Component Name'] == 'Bolting set']['MOC'].dropna().unique().tolist()
    if bolt_mocs:
        bolt_moc = st.selectbox("Bolting Set MOC", bolt_mocs)
        selected_mocs['Bolting set'] = bolt_moc
        
    other_mocs = filtered_df[filtered_df['Component Name'] == 'Other Components Bundle']['MOC'].dropna().unique().tolist()
    if other_mocs:
        default_idx = 0
        if auto_other_moc and auto_other_moc in other_mocs:
            default_idx = other_mocs.index(auto_other_moc)
        other_moc = st.selectbox("Other Components Bundle MOC", other_mocs, index=default_idx)
        selected_mocs['Other Components Bundle'] = other_moc

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

if not sizes:
    st.warning("Please select at least one size at the top to view costs.")
else:
    summary_data = []
    bom_data = {"Component Name": list(selected_mocs.keys()), "MOC Selected": list(selected_mocs.values())}

    for s in sizes:
        size_df = filtered_df[filtered_df['Size'] == s]
        size_costs = []
        total_component_cost = 0.0
        
        for comp, moc in selected_mocs.items():
            try:
                cost_series = size_df[(size_df['Component Name'] == comp) & (size_df['MOC'] == moc)]['Unit Cost (₹)']
                val = float(cost_series.values[0]) if not cost_series.empty else 0.0
            except:
                val = 0.0
            size_costs.append(val)
            total_component_cost += val
            
        bom_data[f"Cost ({s}) ₹"] = size_costs
        final_barestem_cost = total_component_cost * 1.04 
        summary_data.append({"Valve Size": s, "Final Barestem Cost (₹)": f"₹ {final_barestem_cost:,.2f}"})

    st.table(pd.DataFrame(summary_data))

    # --- 6. BILL OF MATERIAL (Hidden in Expander) ---
    if selected_mocs:
        with st.expander("View Bill of Material (BOM) Breakdown", expanded=False):
            st.dataframe(pd.DataFrame(bom_data), use_container_width=True)
