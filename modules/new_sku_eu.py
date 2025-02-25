import streamlit as st
import pandas as pd
from io import BytesIO

def run():
    st.header("EU SKU Validation")
    
    # EU-specific constants
    REQUIRED_ATTRIBUTES = [
        "Family Id", "Import Family Id", "US Hierarchy Category V2", "Material Bank SKU",
        "Material Url", "Product Type", "Configurable Color", "Primary Child", "Configurable Variation Labels",
        "Product Categories", "Product Websites", "Hide From Product View EU", "Visibility EU", "Batch Number",
        "Product Name", "Manufacturer Sku EU", "Color Name", "Color Number", "MBID", "Manufacturer", "Price Range",
        "Commercial & Residential", "Attribute Set Code", "HS Code", "Taxonomy Node", "California Prop 65", "Retired Sku",
        "Serial Sku", "Stealth SKU", "Indoor & Outdoor", "Item Type", "Description", "Color Variety",
        "Color Saturation", "Primary Color Family", "Secondary Color Family", 
        "Metallic Color", "Stone Pattern", "Customs Value", "Commodity Description", 
        "Channel", "Country Permissions", "Country Of Manufacturer"
    ]
    
    EXPECTED_VALUES = {
        "Product Websites": "base",
        "Hide From Product View EU": "Yes",
        "Stealth SKU": "No",
        "Visibility EU": "Catalog",
        "Serial Sku": "No",
        "Retired Sku": "No",
        "Customs Value": "1",
        "Channel": "Europe"
    }
    
    NECESSARY_FIELDS = [
        "Commercial & Residential", "Color Name", "Color Number", "Price Range", 
        "Indoor & Outdoor", "Product Name"
    ]
    
    NON_EMPTY_FIELDS = [
    "Family Id", "Import Family Id", "US Hierarchy Category V2", "Material Bank SKU",
    "Material Url", "Product Type", "Product Categories", "Batch Number", "Manufacturer Sku EU"
    "Manufacturer Sku", "MBID", "Manufacturer", "Attribute Set Code", "Taxonomy Node", "California Prop 65", 
    "Item Type", "Description", "Color Variety", "Color Saturation", "Primary Color Family",
    "Country Of Manufacturer", "Commodity Description", "HS Code"
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
                    if "Manufacturer Sku EU" in df.columns:
                        st.dataframe(empty_df[["Manufacturer Sku EU", field]])
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
                        'invalid_entries': mismatches[["Manufacturer Sku EU",field]]
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
        

    def review_field_values(main_df, sku_df, match_field, necessary_fields):
        """EU-specific field comparison without CatalogItemID logic"""
        try:
            # Convert matching field
            main_df[match_field] = main_df[match_field].astype(str)
            sku_df[match_field] = sku_df[match_field].astype(str)

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
            merged_df = pd.merge(main_df, sku_df, 
                               on=match_field, 
                               suffixes=("_ImportFile", "_SkuList"))

            # Mismatch detection 
            mismatches = []
            for field in necessary_fields:
                col_main = f"{field}_ImportFile"
                col_sku = f"{field}_SkuList"
                
                if col_main in merged_df.columns and col_sku in merged_df.columns:
                    mismatch = merged_df[merged_df[col_main] != merged_df[col_sku]]
                    if not mismatch.empty:
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

    # Same UI components as US with EU-specific matching field
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
            """)
        
        with col2:
            st.markdown("""
            - Indoor & Outdoor
            - Product Name
            - Manufacturer Sku EU
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
        | Updated Manufacturer Sku EU| Manufacturer Sku EU|
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("💡 Tip: Use Excel's 'Find & Replace' to standardize column names before uploading")
        
    with st.expander("🛠️ What This Validation Does (Click to expand)", expanded=False):
        st.markdown("""
         
        ✅ **Template Compliance**  
        _Ensures the import file meets New SKU template requirements_
        
        ✅ **SKU Comparison**: 
        _Identifies missing or extra SKUs in the import file compared to the SKU list_
        
        ✅ **Field Value Comparison**: 
        _Cross-compares key attributes like `Product Name`, `Color Name`, `Price Range` and more to detect discrepancies_
        
        ✅ **Value Compliance**:
        _Validates critical fields contain exact required values (e.g., 'Stealth SKU' must be 'No')_
        
        ✅ **Primary Child Check**: 
        _Flags missing values in the `Primary Child` column and suggests corrections_

        📌 Use this tool to quickly identify discrepancies and ensure data accuracy before importing SKUs.
        """)
        # Add some visual spacing
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # File uploaders
    main_file = st.file_uploader("Upload EU Import File", type=["xlsx", "csv"])
    sku_file = st.file_uploader("Upload EU SKU List", type=["xlsx", "csv"])

    if main_file and sku_file:
        st.subheader("Validation Results")
        
        # Load files
        with st.spinner("Processing EU files..."):
            main_df = load_file(main_file)
            sku_df = load_file(sku_file)

        if main_df is not None and sku_df is not None:
            # 1. Attribute check
            st.write("### Required Attributes Check")
            check_attributes_in_excel(main_df, REQUIRED_ATTRIBUTES)

            # 2. Field comparison
            st.write("### Field Value Comparison")
            review_field_values(main_df, sku_df, "Manufacturer Sku EU", NECESSARY_FIELDS)
            
            # 3. Expected Values Check (NEW)
            st.write("### Expected Values Validation")
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
                        st.dataframe(details["invalid"][["Manufacturer Sku EU", field]])
                        
            # 5. Check for empty 'Primary Child' values
            st.write("### Primary Child Column Check")
            check_primary_child_column(main_df)