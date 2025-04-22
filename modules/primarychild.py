import streamlit as st
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')

def run():
    # Region configuration
    COLUMNS_CONFIG = {
        "US": {
            "columns": [
                "Channels", "Material Bank SKU", "Family Id", "Manufacturer Sku",
                "Product Type", "Product Name", "Color Name", "Color Number",
                "Configurable Color", "Primary Child", "Available Sizes", "Available Finishes","Available Thicknesses",  "Image Url", "Url Key",
                "Color Variety", "Color Saturation", "Primary Color Family"
            ]
        },
        "EU": {
            "columns": [
                "Channels", "Material Bank SKU", "Family Id", "Manufacturer Sku EU",
                "Product Type", "Product Name", "Color Name", "Color Number",
                "Configurable Color", "Primary Child", "Available Sizes", "Available Finishes","Available Thicknesses", "Image Url", "Url Key",
                "Color Variety", "Color Saturation", "Primary Color Family"
            ]
        }
    }

    # UI Components
    region = st.radio(
        "Select Region:",
        ["US", "EU"],
        index=0,
        horizontal=True
    )

    # File Upload Section
    st.write("#### File Uploads")
    export_file = st.file_uploader("Upload PIM Export File", type=["xlsx", "csv"], 
                                 help="Upload the brand export file from PIM")
    ticket_file = st.file_uploader("Upload Change Request File", type=["xlsx", "csv"], 
                                 help="Upload the file with SKUs needing primary child changes")

    identifier_options = ["Material Bank SKU", "Manufacturer Sku", "Product Name"]
    if region == "EU":
        identifier_options.insert(2, "Manufacturer Sku EU")

    identifier_type = st.selectbox(
        "Select Primary Identifier:",
        options=identifier_options,
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
            required_columns = COLUMNS_CONFIG[region]["columns"] + ["Retired Sku", "Stealth SKU"]
            errors = []
            
            # Check required columns in export file
            missing_export_cols = [col for col in required_columns if col not in export_df.columns]
            if missing_export_cols:
                errors.append(f"Missing columns in Export File: {', '.join(missing_export_cols)}")
                
            # Check identifier presence
            if identifier_type not in export_df.columns:
                errors.append(f"'{identifier_type}' column missing in Export File")
            if identifier_type not in ticket_df.columns:
                errors.append(f"'{identifier_type}' column missing in Ticket File")

            if errors:
                st.error("Validation Errors:")
                for error in errors:
                    st.write(f"- {error}")
                return

            # Process data with preserved string types
            ticket_identifiers = ticket_df[identifier_type].str.strip().unique()
            export_df[identifier_type] = export_df[identifier_type].str.strip()
            
            # Get base matches from ticket
            base_matches = export_df[export_df[identifier_type].isin(ticket_identifiers)]
            
            if base_matches.empty:
                st.warning("No matching records found between ticket file and export file")
                return

            # Get family members
            family_ids = base_matches['Family Id'].str.strip().unique()
            family_members = export_df[
                (export_df['Family Id'].str.strip().isin(family_ids)) &
                (export_df['Retired Sku'].str.strip().str.lower() == 'no') &
                (export_df['Stealth SKU'].str.strip().str.lower() == 'no')
            ]

            # Filter and select columns
            result_df = family_members[COLUMNS_CONFIG[region]["columns"]].copy()

            # Preview with highlighting
            st.markdown("---")
            with st.expander("Preview Family Members", expanded=True):
                styled_df = result_df.style.map(
                    lambda x: 'background-color: #FFC7CE' if x == 'Yes' else '', 
                    subset=['Primary Child']
                )
                st.dataframe(styled_df, height=400, use_container_width=True)
                st.caption(f"Total Active Family Members: {len(result_df)}")

            # Excel Export with text preservation
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                result_df.to_excel(writer, sheet_name='Family_Members', index=False)
                
                # Create formats
                workbook = writer.book
                text_format = workbook.add_format({'num_format': '@'})
                highlight_format = workbook.add_format({
                    'num_format': '@',
                    'bg_color': '#FFC7CE'
                })
                
                # Format worksheet
                sheet = writer.sheets['Family_Members']
                pc_col_idx = result_df.columns.get_loc('Primary Child')
                
                # Set text format for all columns
                for idx, col in enumerate(result_df.columns):
                    max_len = max(
                        result_df[col].astype(str).str.len().max(),
                        len(str(col))
                    ) + 2
                    sheet.set_column(idx, idx, min(max_len, 30), text_format)
                
                # Apply highlights
                for row in range(1, len(result_df) + 1):
                    if result_df.iloc[row-1]['Primary Child'] == 'Yes':
                        sheet.write(row, pc_col_idx, 'Yes', highlight_format)
                
                sheet.autofilter(0, 0, len(result_df), len(result_df.columns)-1)

            st.success("Processing complete! Download family members list:")
            st.download_button(
                label="Download Report",
                data=output.getvalue(),
                file_name=f"primary_child_candidates_{region}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Processing error: {str(e)}")

if __name__ == "__main__":
    run()