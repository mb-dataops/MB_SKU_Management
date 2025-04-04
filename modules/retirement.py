import streamlit as st
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')

def run():
    # Region configuration
    RETIRE_COLUMNS = {
        "US": {
            "retire_columns": [
                "Channel", "Material Bank SKU", "Family Id", "Manufacturer Sku",
                "Product Type", "Product Name", "Primary Child", "Url Key",
                "Stealth SKU", "Retired Sku", "Admin Notes", "Inventory Disposition",
                "Visibility", "Hide From Product View"
            ],
            "reassign_columns": [
                "Channel", "Material Bank SKU", "Family Id", "Manufacturer Sku",
                "Product Type", "Product Name", "Color Name", "Color Number",
                "Configurable Color", "Primary Child", "Image Url", "Url Key", "Primary Color Family",
                "Color Variety", "Color Saturation", "Retired Sku", "Admin Notes",
                "Inventory Disposition", "Visibility", "Hide From Product View"
            ],
            "visibility_col": "Visibility",
            "hide_col": "Hide From Product View"
        },
        "EU": {
            "retire_columns": [
                "Channel", "Material Bank SKU", "Family Id", "Manufacturer Sku EU",
                "Product Type", "Product Name", "Primary Child", "Url Key",
                "Stealth SKU", "Retired Sku", "Admin Notes", "Inventory Disposition",
                "Visibility EU", "Hide From Product View EU"
            ],
            "reassign_columns": [
                "Channel", "Material Bank SKU", "Family Id", "Manufacturer Sku EU",
                "Product Type", "Product Name", "Color Name", "Color Number",
                "Configurable Color", "Primary Child", "Image Url", "Url Key", "Primary Color Family",
                "Color Variety", "Color Saturation", "Retired Sku", "Admin Notes",
                "Inventory Disposition", "Visibility EU", "Hide From Product View EU"
            ],
            "visibility_col": "Visibility EU",
            "hide_col": "Hide From Product View EU"
        }
    }

    # UI Components
    col1, col2 = st.columns(2)
    with col1:
        region = st.radio(
            "Select Region:",
            ["US", "EU"],
            index=0,
            horizontal=True
        )
    with col2:
        initials = st.selectbox(
            "Select Your Initials:",
            options=["AL", "FH", "JL", "LL", "TO"],
            index=1  # Default to FH
        )
    
    # File Upload Section
    st.write("#### File Uploads")
    with st.expander("📋 **Upload Instructions (Click to Expand)**", expanded=False):
        st.markdown("""
        ### Essential Checks Before Uploading:
        
        ⚠️ **Important:** Field Name Consistency
        
        Ensure the primary identifier field matches exactly in both files
        """)

    export_file = st.file_uploader("Upload PIM Export File", type=["xlsx", "csv"], 
                                 help="Upload the brand export file from PIM")
    ticket_file = st.file_uploader("Upload Retirement Ticket File", type=["xlsx", "csv"], 
                                 help="Upload the file with SKUs to be retired")
    
    identifier_type = st.selectbox(
        "Select Primary Identifier:",
        options=["Material Bank SKU", "Manufacturer Sku", "Manufacturer Sku EU", "Product Name"],
        index=0,
        help="Select the primary identifier for filtering SKUs"
    )

    if export_file and ticket_file:
        try:
            # Modified data loading with string preservation
            def read_file_with_strings(file):
                """Read file while preserving number-like strings"""
                if file.name.endswith('.xlsx'):
                    return pd.read_excel(file, dtype=str)
                else:
                    return pd.read_csv(file, dtype=str)

            # Load data as strings
            export_df = read_file_with_strings(export_file)
            ticket_df = read_file_with_strings(ticket_file)

            # Clean data while preserving types
            def clean_string_series(series):
                """Clean values while maintaining data type"""
                return series.str.strip() if series.dtype == 'object' else series

            export_df = export_df.apply(clean_string_series)
            ticket_df = ticket_df.apply(clean_string_series)

            # Validation checks
            required_columns = list(set(
                RETIRE_COLUMNS[region]["retire_columns"] +
                RETIRE_COLUMNS[region]["reassign_columns"] +
                ["Family Id", "Primary Child"]
            ))
            
            missing_columns = [col for col in required_columns if col not in export_df.columns]
            errors = []
            if missing_columns:
                errors.append(f"Missing columns in Export File: {', '.join(missing_columns)}")
            if identifier_type not in export_df.columns:
                errors.append(f"'{identifier_type}' column missing in Export File")
            if identifier_type not in ticket_df.columns:
                errors.append(f"'{identifier_type}' column missing in Ticket File")
            if not initials:
                errors.append("Please select your initials")

            if errors:
                st.error("Validation Errors:")
                for error in errors:
                    st.write(f"- {error}")
                return

            # Process data with preserved string types
            ticket_identifiers = ticket_df[identifier_type].str.strip().unique()
            export_df[identifier_type] = export_df[identifier_type].str.strip()
            
            # Get base matches
            base_matches = export_df[export_df[identifier_type].isin(ticket_identifiers)].copy()
            final_results = base_matches[RETIRE_COLUMNS[region]["retire_columns"]].copy()
            
            # Update Final Results fields
            final_results['Retired Sku'] = 'Yes'
            final_results[RETIRE_COLUMNS[region]["visibility_col"]] = 'Not Visible Individually'
            final_results[RETIRE_COLUMNS[region]["hide_col"]] = 'Yes'
            final_results['Admin Notes'] = f"Ticket X, Retired - {initials}"

            # Only run reassignment logic if identifier is NOT Product Name
            family_skus_filtered = pd.DataFrame()
            if identifier_type != "Product Name":
                # ReassignPrimaryChild logic
                primary_yes = base_matches[base_matches['Primary Child'] == 'Yes'].copy()
                family_ids = primary_yes['Family Id'].str.strip().unique()
                family_skus = export_df[export_df['Family Id'].str.strip().isin(family_ids)].copy()
                family_skus = family_skus[family_skus['Retired Sku'].str.strip().str.lower() == 'no']
                family_skus_filtered = family_skus[RETIRE_COLUMNS[region]["reassign_columns"]].copy()

            # Preview with highlighting
            st.markdown("---")
            with st.expander("Preview Final Results", expanded=True):
                styled_final = final_results.style.map(
                    lambda x: 'background-color: red' if x == 'Yes' else '', 
                    subset=['Primary Child']
                )
                st.dataframe(styled_final, height=300, use_container_width=True)
                st.caption(f"Primary Records: {len(final_results)}")

            # Only show reassignment preview if needed
            if identifier_type != "Product Name" and not family_skus_filtered.empty:
                with st.expander("Preview Reassignment Candidates", expanded=False):
                    ticket_skus = set(ticket_identifiers)
                    styled_reassign = family_skus_filtered.style.map(
                        lambda x: 'background-color: #90EE90' if str(x) in ticket_skus else '',
                        subset=['Material Bank SKU']
                    )
                    st.dataframe(styled_reassign, height=300, use_container_width=True)
                    st.caption(f"Active Family Members: {len(family_skus_filtered)}")

            # Excel Export with text preservation
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Create formats
                workbook = writer.book
                text_format = workbook.add_format({'num_format': '@'})
                red_format = workbook.add_format({'num_format': '@', 'bg_color': '#FFC7CE'})
                
                # Final Results sheet
                final_results.to_excel(writer, sheet_name='Final_Results', index=False)
                final_sheet = writer.sheets['Final_Results']
                pc_col_idx = final_results.columns.get_loc('Primary Child')
                
                # Only create reassignment sheet if needed
                if identifier_type != "Product Name" and not family_skus_filtered.empty:
                    green_format = workbook.add_format({'num_format': '@', 'bg_color': '#90EE90'})
                    family_skus_filtered.to_excel(writer, sheet_name='ReassignPrimaryChild', index=False)
                    reassign_sheet = writer.sheets['ReassignPrimaryChild']
                    sku_col_idx = family_skus_filtered.columns.get_loc('Material Bank SKU')

                # Format columns and apply highlighting
                for sheet, df in [(final_sheet, final_results)]:
                    for idx, col in enumerate(df.columns):
                        max_len = max(df[col].str.len().max(), len(col)) + 2
                        sheet.set_column(idx, idx, min(max_len, 30), text_format)
                    sheet.autofilter(0, 0, len(df), len(df.columns)-1)

                # Apply highlights to final results
                for row in range(1, len(final_results)+1):
                    if final_results.iloc[row-1]['Primary Child'] == 'Yes':
                        final_sheet.write(row, pc_col_idx, 'Yes', red_format)

                # Apply highlights to reassignment sheet if exists
                if identifier_type != "Product Name" and not family_skus_filtered.empty:
                    for row in range(1, len(family_skus_filtered)+1):
                        current_sku = family_skus_filtered.iloc[row-1]['Material Bank SKU']
                        if current_sku in ticket_identifiers:
                            reassign_sheet.write(row, sku_col_idx, current_sku, green_format)
                    # Format reassignment sheet columns
                    for idx, col in enumerate(family_skus_filtered.columns):
                        max_len = max(family_skus_filtered[col].str.len().max(), len(col)) + 2
                        reassign_sheet.set_column(idx, idx, min(max_len, 30), text_format)
                    reassign_sheet.autofilter(0, 0, len(family_skus_filtered), len(family_skus_filtered.columns)-1)

            st.success("Processing complete! Download results:")
            st.download_button(
                label="Download Report",
                data=output.getvalue(),
                file_name=f"sku_retirement_{region}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Processing error: {str(e)}")

if __name__ == "__main__":
    run()