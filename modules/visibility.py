import streamlit as st
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')

def run():
    
    # Region configuration
    REGION_CONFIG = {
        "US": {
            "filter_columns": ["Material Bank SKU", "Enable Product", "Family Id", "Manufacturer Sample Id",
                             "Product Finish Type", "Associated Finishes", "Manufacturer Sku", "Product Type",
                             "Stealth SKU", "Visibility", "Hide From Product View", "Approximate Sample Size",
                             "State Permission", "Product Name", "Channels"]
        },
        "EU": {
            "filter_columns": ["Material Bank SKU", "Enable Product", "Family Id", "Manufacturer Sample Id",
                             "Product Finish Type", "Associated Finishes", "Manufacturer Sku EU", "Product Type",
                             "Stealth SKU", "Visibility EU", "Hide From Product View EU", "Approximate Sample Size",
                             "State Permission", "Product Name", "Channels"]
        }
    }
    
    # Region selection radio buttons
    region = st.radio(
        "Select Region:",
        ["US", "EU"],
        index=0,  # Default to US
        horizontal=True
    )

    # File Upload Section
    st.write("#### File Uploads")
    with st.expander("📋 **Upload Instructions (Click to Expand)**", expanded=False):
        st.markdown("""
        ### Essential Checks Before Uploading:
        
        ⚠️ **Important:**  Field Name Consistency
        
        Ensure the primary identifier field you select below matches **exactly** in both files for correct filtering.
        """)
    
    # File uploaders
    export_file = st.file_uploader(
        "Upload the PIM Export File (Excel/CSV)", 
        type=["xlsx", "csv"],
        help="Upload the brand export file from PIM"
    )
    
    ticket_file = st.file_uploader(
        "Upload the Ticket file (Excel/CSV)", 
        type=["xlsx", "csv"],
        help="Upload the ticket file with SKUs to be visible"
    )

    # Identifier type dropdown
    identifier_type = st.selectbox(
        "Select Identifier Type:",
        options=["Material Bank SKU", "Manufacturer Sku","Manufacturer Sku EU", "Batch Number", "Product Name"],
        index=0,
        help="Select the primary identifier for filtering SKUs"
    )

    # Add visual separation
    st.markdown("---")
    
    # Rest of your processing logic can go here
    if export_file and ticket_file:
        try:
            # Load data
            export_df = pd.read_excel(export_file) if export_file.name.endswith('.xlsx') else pd.read_csv(export_file)
            ticket_df = pd.read_excel(ticket_file) if ticket_file.name.endswith('.xlsx') else pd.read_csv(ticket_file)

            # Validation checks
            errors = []
            
            if identifier_type not in export_df.columns:
                errors.append(f"'{identifier_type}' column missing in Export File")
            if identifier_type not in ticket_df.columns:
                errors.append(f"'{identifier_type}' column missing in Ticket File")
            
            required_columns = REGION_CONFIG[region]["filter_columns"]
            missing_columns = [col for col in required_columns if col not in export_df.columns]
            if missing_columns:
                errors.append(f"Missing columns in Export File: {', '.join(missing_columns)}")

            if errors:
                st.error("Validation Errors:")
                for error in errors:
                    st.write(f"- {error}")
                return

            # Process data
            ticket_identifiers = ticket_df[identifier_type].astype(str).str.strip().unique()
            export_df[identifier_type] = export_df[identifier_type].astype(str).str.strip()
            
            # Get original matches
            original_matches = export_df[export_df[identifier_type].isin(ticket_identifiers)]
            
            # Find parent SKUs
            parent_rows = pd.DataFrame()
            if not original_matches.empty:
                family_ids = original_matches['Family Id'].dropna().astype(str).unique()
                if len(family_ids) > 0:
                    parent_condition = (
                        export_df['Family Id'].astype(str).isin(family_ids) &
                        export_df['Product Type'].str.strip().str.lower().eq('configurable'))
                    parent_rows = export_df[parent_condition]

            # Combine results and remove duplicates
            combined_df = pd.concat([original_matches, parent_rows]).drop_duplicates()

            # Create final filtered dataset
            filtered_final = combined_df[required_columns].copy()
            
            # Apply business logic to Final Results
            if not filtered_final.empty:
                # Determine region-specific column names
                if region == "US":
                    hide_col = "Hide From Product View"
                    visibility_col = "Visibility"
                else:
                    hide_col = "Hide From Product View EU"
                    visibility_col = "Visibility EU"

                # 1. Set 'Hide From Product View' to 'No'
                filtered_final[hide_col] = 'No'

                # 2. Update 'Visibility' based on Product Type
                # Clean Product Type values
                product_type_clean = filtered_final['Product Type'].str.strip().str.lower()
                
                # Create masks
                mask_configurable = product_type_clean == 'configurable'
                mask_simple = product_type_clean == 'simple'

                # Apply visibility rules
                filtered_final.loc[mask_configurable, visibility_col] = "Catalog, Search"
                filtered_final.loc[mask_simple, visibility_col] = "Catalog"


            # Create Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # 1st tab Final Results 
                filtered_final.to_excel(writer, sheet_name='Final Results', index=False)
                
                # 2nd tab Filtered Rows 
                combined_df.to_excel(writer, sheet_name='Filtered Rows', index=False)

                # Auto-format columns
                for sheet_name in ['Final Results', 'Filtered Rows']:
                    worksheet = writer.sheets[sheet_name]
                    df = filtered_final if sheet_name == 'Final Results' else combined_df
                    
                    for idx, col in enumerate(df.columns):
                        max_len = max(
                            df[col].astype(str).str.len().max(),
                            len(str(col))
                        ) + 2
                        worksheet.set_column(idx, idx, min(max_len, 50))
                    worksheet.autofilter(0, 0, len(df), len(df.columns)-1)
                    
            # Create preview section        
            if not filtered_final.empty:
                with st.expander("Preview Final Results", expanded=False):
                    st.dataframe(
                        filtered_final,
                        use_container_width=True,
                        height=300
                    )
                    st.caption(f"Showing all {len(filtered_final)} records")

            st.success("Processing complete! Download results:")
            st.download_button(
                label="Download Excel File",
                data=output.getvalue(),
                file_name=f"sku_visibility_{region}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Processing error: {str(e)}")