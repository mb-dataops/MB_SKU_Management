import streamlit as st
import pandas as pd
from io import BytesIO

def run():
    st.header("Stealth SKU Validation")
    
    REQUIRED_COLUMNS = [
        "Material Bank SKU", "Batch Number", "Product Type", "Primary Child", "Product Websites", 
        "Hide From Product View", "Stealth SKU", "Visibility", "MBID", "Manufacturer", 
        "Attribute Set Code", "Taxonomy Node", "Product Categories", "Manufacturer Sku", 
        "Product Name", "Color Name", "Material Url", "Price Range", "California Prop 65", 
        "Serial Sku", "Retired Sku", "Commercial & Residential", "Indoor & Outdoor", 
        "Is Fulfillment SKU"
    ]

    EXPECTED_VALUES = {
        "Product Type": "simple",
        "Primary Child": "No",
        "Product Websites": "base",
        "Hide From Product View": "Yes",
        "Stealth SKU": "Yes",
        "Visibility": "Not Visible Individually",
        "Serial Sku": "No",
        "Retired Sku": "No"
    }

    def load_file(uploaded_file):
        try:
            if uploaded_file.name.endswith('.xlsx'):
                return pd.read_excel(uploaded_file, engine='openpyxl')
            elif uploaded_file.name.endswith('.csv'):
                return pd.read_csv(uploaded_file)
            return None
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return None

    # File Upload Section
    with st.expander("📋 Upload Instructions (Click to expand)", expanded=False):
        st.markdown("""
        **Required Files:**
        - Stealth SKU Import File (Excel/CSV)
        - SKU List File (Excel/CSV)
        
        **Essential Check Before Uploading:**
        - Ensure 'Sample SKU' field exist in the SKU List File
        """)
        
    #  Validation Overview Section
    with st.expander("🛠️ What This Validation Does (Click to expand)", expanded=False):
        st.markdown("""
    
        ✅ **Template Compliance**  
        _Ensures the import file meets Stealth SKU template requirements_
        
        ✅ **Data Integrity**  
        _Validates expected field values in the import file_
        
        ✅ **SKU Reconciliation**  
        _Verifies alignment between Sample SKUs and Manufacturer SKUs in the SKU list and the import file_
        
        📌 Use this tool to quickly identify discrepancies and ensure data accuracy before importing SKUs.
        """)
        
        # Add some visual spacing
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        main_file = st.file_uploader("Stealth Import File", type=["xlsx", "csv"])
    with col2:
        sku_file = st.file_uploader("SKU List File", type=["xlsx", "csv"])

    if main_file and sku_file:
        with st.spinner("Validating files..."):
            df_main = load_file(main_file)
            df_sku = load_file(sku_file)

            if df_main is not None and df_sku is not None:
                # 1. Required Columns Check
                missing_cols = [col for col in REQUIRED_COLUMNS if col not in df_main.columns]
                if missing_cols:
                    st.error("Missing required columns:")
                    st.write(missing_cols)
                else:
                    st.success("✅ All required columns present")

                # 2. Expected Values Validation
                st.subheader("Field Value Validation")
                invalid_counts = 0
                for field, expected in EXPECTED_VALUES.items():
                    if field in df_main.columns:
                        invalid = df_main[df_main[field].astype(str) != expected]
                        if not invalid.empty:
                            invalid_counts += 1
                            with st.expander(f"⚠️ Invalid {field} values", expanded=False):
                                st.write(f"Expected: {expected}")
                                st.dataframe(invalid[["Material Bank SKU", field]])
                
                if invalid_counts == 0:
                    st.success("✅ All field values match expected values")

                # 3. Sample SKU Validation
                st.subheader("Sample SKU Check")
                if "Sample SKU" in df_sku.columns and "Manufacturer Sku" in df_main.columns:
                    sample_skus = set(df_sku["Sample SKU"].astype(str).str.strip())
                    manufacturer_skus = set(df_main["Manufacturer Sku"].astype(str).str.strip())
                    
                    # Check both directions
                    missing = sample_skus - manufacturer_skus
                    extra = manufacturer_skus - sample_skus
                    
                    # Missing SKUs
                    if missing:
                        st.error(f"🚨 Missing {len(missing)} Sample SKUs in Import File")
                        with st.expander("View missing SKUs"):
                            st.write(list(missing))
                    else:
                        st.success("✅ All Sample SKUs present in Manufacturer Sku")
                        
                    # Extra SKUs
                    if extra:
                        st.warning(f"⚠️ Found {len(extra)} unexpected SKUs in Import File")
                        with st.expander("View extra SKUs"):
                            st.write(list(extra))
                    else:
                        st.success("✅ No unexpected SKUs found in Import File")
                        
                    st.metric("Unique Sample SKUs", df_sku["Sample SKU"].nunique())
                else:
                    st.warning("Missing required columns for Sample SKU validation")