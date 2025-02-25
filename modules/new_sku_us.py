import streamlit as st
import pandas as pd
from io import BytesIO
import json
from pathlib import Path

""" Code structure:

Streamlit UI Setup**: The `run()` function initializes the UI, defines constants, and handles file uploads.

File Loading**: The `load_file` function reads Excel or CSV files.

Attribute Check**: `check_attributes_in_excel` verifies if all required columns are present.

Field Comparison**: `review_field_values` merges dataframes, checks for mismatches, and handles configurable products appropriately.

Handling Configurable Products**: The logic skips CatalogItemID validation for configurable products by filtering those rows during comparison. """

def run():
    st.header("US SKU Validation")
    
    # Define constants
    REQUIRED_ATTRIBUTES = [
        "CatalogItemID", "Family Id", "Import Family Id", "US Hierarchy Category V2", "Material Bank SKU",
        "Material Url", "Product Type", "Configurable Color", "Primary Child", "Configurable Variation Labels",
        "Product Categories", "Product Websites", "Hide From Product View", "Visibility", "Batch Number",
        "Product Name", "Manufacturer Sku", "Color Name", "Color Number", "MBID", "Manufacturer", "Price Range",
        "Commercial & Residential", "Attribute Set Code", "Taxonomy Node", "California Prop 65", "Retired Sku",
        "Serial Sku", "Stealth SKU", "Indoor & Outdoor", "Set as New SKU", "Item Type", "Description", "Color Variety",
        "Color Saturation", "Primary Color Family", "Secondary Color Family",
        "Metallic Color", "Stone Pattern"
    ]
    
    EXPECTED_VALUES = {
        "Product Websites": "base",
        "Hide From Product View": "Yes",
        "Stealth SKU": "No",
        "Visibility": "Catalog",
        "Serial Sku": "No",
        "Retired Sku": "No"
    }
    
    NECESSARY_FIELDS = [
        "Commercial & Residential", "Color Name", "Color Number", "Price Range", 
        "California Prop 65", "Indoor & Outdoor", "CatalogItemID", "Product Name", 
        "Set as New SKU"
    ]
    
    NON_EMPTY_FIELDS = [
    "Family Id", "Import Family Id", "US Hierarchy Category V2", "Material Bank SKU",
    "Material Url", "Product Type", "Product Categories", "Batch Number", 
    "Manufacturer Sku", "MBID", "Manufacturer", "Attribute Set Code", "Taxonomy Node", "California Prop 65", 
    "Item Type", "Description", "Color Variety", "Color Saturation", "Primary Color Family"
    ]
    
    FIELD_PATTERNS = {
        "Batch Number": {
            "pattern": r'^Batch \d{3}(?:-\d{2})?$',
            "example": "Batch 001 or Batch 001-01"       # Example format for error messages
        }
    }

    def check_attributes_in_excel(df, required_attributes):
        """Check for missing attributes in the uploaded file"""
        columns_in_sheet = df.columns.tolist()
        missing_attributes = [attr for attr in required_attributes if attr not in columns_in_sheet]
        
        if not missing_attributes:
            st.success("All required attributes are present in the sheet.")
        else:
            st.error("Missing attributes detected:")
            for attr in missing_attributes:
                st.write(f"- {attr}")
                
    def check_non_empty_fields(df, fields_to_check):
        """Check for empty values in specified fields and alert the user."""
        errors = {}
        for field in fields_to_check:
            if field in df.columns:
                # Check for NaN or empty strings
                empty_mask = df[field].isna() | (df[field].astype(str).str.strip() == '')
                empty_rows = df[empty_mask]
                if not empty_rows.empty:
                    errors[field] = empty_rows
        
        if errors:
            st.warning("⚠️ Empty values detected in required fields!")
            for field, empty_df in errors.items():
                with st.expander(f"Empty values in '{field}'"):
                    st.write(f"Number of empty entries: {len(empty_df)}")
                    if "Manufacturer Sku" in df.columns:
                        st.dataframe(empty_df[["Manufacturer Sku", field]])
                    else:
                        st.dataframe(empty_df[field])
        
            
    def validate_field_patterns(df):
        """Validate field values against required patterns"""
        errors = {}
        for field, config in FIELD_PATTERNS.items():
            if field in df.columns:
                # Convert to string and strip whitespace for validation
                cleaned_series = df[field].astype(str).str.strip()
                
                # Create mask for invalid entries
                invalid_mask = ~cleaned_series.str.match(config["pattern"])
                invalid_entries = df[invalid_mask]
                
                if not invalid_entries.empty:
                    errors[field] = {
                        "invalid": invalid_entries,
                        "example": config["example"]
                    }
        return errors

                
    def check_expected_values(df, expected_values):
        """Validate field values match expected requirements"""
        errors = {}
        for field, expected in expected_values.items():
            if field in df.columns:
                # Find mismatches (case-sensitive comparison)
                mismatches = df[df[field].astype(str) != expected]
                if not mismatches.empty:
                    errors[field] = {
                        'expected': expected,
                        'invalid_entries': mismatches[["Manufacturer Sku",field]]
                    }
        return errors

    def load_file(uploaded_file):
        """Load uploaded file into DataFrame"""
        try:
            if uploaded_file.name.endswith('.xlsx'):
                return pd.read_excel(uploaded_file, engine='openpyxl')
            elif uploaded_file.name.endswith('.csv'):
                return pd.read_csv(uploaded_file)
            else:
                st.error("Unsupported file type. Please upload .xlsx or .csv")
                return None
        except Exception as e:
            st.error(f"Error loading file: {e}")
            return None
        
    

    def review_field_values(main_df, sku_df, match_field, necessary_fields):
        """Compare values between Import file and SKU list"""
        try:
            # Convert matching field to string type
            main_df[match_field] = main_df[match_field].astype(str)
            sku_df[match_field] = sku_df[match_field].astype(str)

            
            # # Identify configurable rows but keep CatalogItemID in necessary_fields
            # configurable_mask = None
            # if 'Product Type' in main_df.columns:
            #  configurable_mask = main_df['Product Type'].str.lower() == 'configurable'
            # Store configurable status before merge
            main_df = main_df.copy()
            if 'Product Type' in main_df.columns:
             main_df['_is_configurable'] = main_df['Product Type'].str.lower() == 'configurable'
            else:
             main_df['_is_configurable'] = False


            # SKU comparisons
            main_skus = set(main_df[match_field])
            sku_skus = set(sku_df[match_field])

            with st.expander("SKU Comparison Results"):
                # Check missing SKUs in Import file
                missing_in_main = sku_skus - main_skus
                if missing_in_main:
                    st.warning("SKUs missing in the Import file:")
                    st.write(list(missing_in_main))

                # Check extra SKUs in Import file
                extra_in_main = main_skus - sku_skus
                if extra_in_main:
                    st.warning("Extra SKUs in the Import file:")
                    st.write(list(extra_in_main))

            # Merge dataframes
            merged_df = pd.merge(main_df, sku_df, on=match_field, suffixes=("_ImportFile", "_SkuList"))
            
            # Force string type for CatalogItemID comparison
            if 'CatalogItemID_ImportFile' in merged_df.columns:
             merged_df['CatalogItemID_ImportFile'] = merged_df['CatalogItemID_ImportFile'].astype(str)
            if 'CatalogItemID_SkuList' in merged_df.columns:
             merged_df['CatalogItemID_SkuList'] = merged_df['CatalogItemID_SkuList'].astype(str)

            mismatches = []
            for field in necessary_fields:
             col_main = f"{field}_ImportFile"
             col_sku = f"{field}_SkuList"
            
             if col_main in merged_df.columns and col_sku in merged_df.columns:
                 # Handle CatalogItemID specially for configurable products
                # if field == 'CatalogItemID' and configurable_mask is not None:
                #     # Only validate NON-configurable rows for CatalogItemID
                #     temp_df = merged_df[~configurable_mask.reindex(merged_df.index, fill_value=False)]
                # else:
                #     temp_df = merged_df
                if field == 'CatalogItemID':
                    temp_df = merged_df[~merged_df['_is_configurable']]
                else:
                    temp_df = merged_df
                
                # Find mismatches
                mismatch = temp_df[temp_df[col_main] != temp_df[col_sku]]
                
                # mismatch = merged_df[merged_df[col_main] != merged_df[col_sku]]
                if not mismatch.empty:
                    # Store field-specific columns
                    mismatches.append((
                        field, 
                        mismatch[[match_field, col_main, col_sku]]
                    ))

            # Display results
            if not mismatches:
             st.success("All necessary fields match between files!")
            else:
             st.error("Field mismatches detected:")
             for field, mismatch_df in mismatches:
                with st.expander(f"Mismatches in {field}"): 
                    st.write(f"Comparison between Import File and SKU List for {field}")
                    st.dataframe(mismatch_df)

        except Exception as e:
            st.error(f"Comparison error: {str(e)}")
            
    def check_primary_child_column(df):
        """Check for empty values in Primary Child column and alert the user."""
        if "Primary Child" in df.columns and "Material Bank SKU" in df.columns:
            empty_primary_child = df[df["Primary Child"].isna()]

            if not empty_primary_child.empty:
                st.warning("⚠️ Empty values detected in 'Primary Child' column!")
                st.write("To maintain uniformity, consider adding 'No' for non-primary child SKUs.")

                # Convert 'Material Bank SKU' to string to prevent number formatting issues
                empty_primary_child = df[df["Primary Child"].isna()].copy()
                empty_primary_child["Material Bank SKU"] = empty_primary_child["Material Bank SKU"].astype(str)
                
                st.dataframe(empty_primary_child[["Material Bank SKU", "Primary Child"]])
                
            else:
                st.info("✅ No action needed! Primary Child field is populated.")
                

    def load_state_permission_brands():
        """Load state permission required manufacturers"""
        try:
            path = Path(__file__).resolve().parent.parent / "constants" / "state_permission_brands.json"
            with open(path) as f:
                return json.load(f)
        except FileNotFoundError:
            st.error("State permission brand list not found")
            st.error("Constants folder structure: " + str(Path(__file__).resolve()))
            return []
        except json.JSONDecodeError:
            st.error("Invalid state permission brand list format")
            return []

    def validate_state_permissions(df, required_brands):
        """Check state permission requirements"""
        alerts = []
        
        # Check if manufacturer column exists
        if "Manufacturer" not in df.columns:
            return alerts
        
        # Find matching manufacturers
        state_brand_mask = df["Manufacturer"].isin(required_brands)
        state_brands = df[state_brand_mask]
        
        if not state_brands.empty:
            # Check if State Permission column exists
            if "State Permission" not in df.columns:
                alerts.append({
                    "type": "missing_column",
                    "brands": state_brands["Manufacturer"].unique().tolist()
                })
            else:
                # Check for empty values
                invalid = state_brands[state_brands["State Permission"].isna() | 
                                    (state_brands["State Permission"] == "")]
                if not invalid.empty:
                    alerts.append({
                        "type": "missing_values",
                        "data": invalid[["Material Bank SKU", "Manufacturer", "State Permission"]]
                    })
        
        return alerts


    # Streamlit UI Components
    st.subheader("File Uploads")
    
    with st.expander("📋 **Upload Instructions (Click to Expand)**", expanded=False):
        st.markdown("""
        ### Essential Checks Before Uploading:
        
        🔍 **Field Name Consistency**  
        Ensure these fields match **exactly** in both files:
        """)
        
        # Column layout for field list
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            - Commercial & Residential
            - Color Name
            - Color Number
            - Price Range
            - California Prop 65
            """)
        
        with col2:
            st.markdown("""
            - Indoor & Outdoor
            - CatalogItemID
            - Product Name
            - Set as New SKU
            """)
        
        st.markdown("""
        ### Field Renaming Guide
        ⚠️ **Important:** If your SKU List contains these columns, rename them:
        """)
        
        # Renaming table
        st.markdown("""
        | Original Name | Rename To |
        |---------------|-----------|
        | Updated Product Name | Product Name |
        | Updated Color Name | Color Name |
        | Updated Manufacturer Sku | Manufacturer Sku |
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("💡 Tip: Use Excel's 'Find & Replace' to standardize column names before uploading")
     
     #  Validation Overview Section
    with st.expander("🛠️ What This Validation Does (Click to expand)", expanded=False):
        st.markdown("""
         
        ✅ **Template Compliance**  
        _Ensures the import file meets New SKU template requirements_
        
        ✅ **SKU Comparison**: 
        _Identifies missing or extra SKUs in the import file compared to the SKU list_
        
        ✅ **Field Value Comparison**: 
        _Cross-compares key attributes like `CatalogItemID`, `Product Name`, `Color Name`, and more to detect discrepancies_
        
        ✅ **Value Compliance**:
        _Validates critical fields contain exact required values (e.g., 'Stealth SKU' must be 'No')_
        
        ✅ **Primary Child Check**: 
        _Flags missing values in the `Primary Child` column and suggests corrections_
        
        ✅ **State Permissions**:
        _Ensure brands with state permissions have the "State Permission" field added and populated in the import file_

        📌 Use this tool to quickly identify discrepancies and ensure data accuracy before importing SKUs.
        """)
        # Add some visual spacing
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    
    # File uploaders
    main_file = st.file_uploader("Upload the Import File (Excel/CSV)", type=["xlsx", "csv"])
    sku_file = st.file_uploader("Upload the SKU List File (Excel/CSV)", type=["xlsx", "csv"])

    if main_file and sku_file:
        st.subheader("Validation Results")
        
        # Load files
        with st.spinner("Loading files..."):
            main_df = load_file(main_file)
            sku_df = load_file(sku_file)

        if main_df is not None and sku_df is not None:
            # 1. Attribute check
            st.write("#### Required Attributes Check")
            check_attributes_in_excel(main_df, REQUIRED_ATTRIBUTES)

            # 2. Field comparison
            st.write("#### Field Value Comparison")
            review_field_values(main_df, sku_df, "Manufacturer Sku", NECESSARY_FIELDS)
            
            # 3. Expected Values Check (NEW)
            st.write("#### Expected Values Validation")
            value_errors = check_expected_values(main_df, EXPECTED_VALUES)
            
            if not value_errors:
                st.success("✅ All expected values match requirements")
            else:
                st.error(f"Found {len(value_errors)} fields with invalid values")
                for field, details in value_errors.items():
                    with st.expander(f"Invalid {field} values", expanded=False):
                        st.write(f"Expected Value: {details['expected']}")
                        st.dataframe(details['invalid_entries'])
            
            # 4. Check for required fields non-emptiness           
            check_non_empty_fields(main_df, NON_EMPTY_FIELDS)
            
            #Check Batch number format
            pattern_errors = validate_field_patterns(main_df)
            if pattern_errors:
                for field, details in pattern_errors.items():
                    st.error(f"Invalid format in '{field}'. Expected format: {details['example']}")
                    with st.expander(f"View invalid {field} entries"):
                        st.dataframe(details["invalid"][["Manufacturer Sku", field]])
            
            # 5. Check for empty 'Primary Child' values
            st.write("#### Primary Child Column Check")
            check_primary_child_column(main_df)
            
            # 6. State Permission validation
            st.write("#### State Permission Check")
            try:
                state_brands = load_state_permission_brands()
                # First check if Manufacturer column exists
                if "Manufacturer" in main_df.columns:
                   has_state_brands = main_df["Manufacturer"].isin(state_brands).any()
                   if has_state_brands:
                        permission_alerts = validate_state_permissions(main_df, state_brands)

                        # Display results
                        if permission_alerts:
                         st.warning("⚠️ State Permission Requirements")
                         for alert in permission_alerts:
                            if alert["type"] == "missing_column":
                                st.error(f"Missing 'State Permission' column for the brand {(alert['brands'])} which has state permissions. Ensure the column is added and populated in the import file.")
                            elif alert["type"] == "missing_values":
                                st.error(f"Found {len(alert['data'])} records with missing State Permissions")
                                with st.expander("View records needing updates"):
                                    st.dataframe(alert["data"])
                        else:
                         st.success("✅ State permission requirements met for the brand")
                   else:
                     st.success("✅ This Brand doesn't have State Permissions. No further actions needed")         
                    
            except Exception as e:
               st.error(f"State permission validation error: {str(e)}")