import streamlit as st
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl.styles.stylesheet')

def run():
    
    # Instructions
    with st.expander("📋 **Filtering Instructions**", expanded=False):
        st.markdown("""
        **How to Use:**
        1. Upload your main export file (Excel/CSV)
        2. Upload your filter file containing identifier columns
        3. Select filtering mode (SKU or Family)
        4. Download filtered results with original raw data

        **Modes:**
        - **Filter by SKU:** Matches records directly from filter values
        - **Filter by Family:** Finds all family members of filtered SKUs
        """)

    # Add filter mode selection
    filter_mode = st.radio(
        "Select Filter Mode:",
        ["Filter by SKU", "Filter by Family"],
        index=0,
        horizontal=True
    )

    # File upload section
    col1, col2 = st.columns(2)
    with col1:
        main_file = st.file_uploader(
            "Main Data File",
            type=["xlsx", "csv"],
            help="Upload file containing all records"
        )
    with col2:
        filter_file = st.file_uploader(
            "Filter File",
            type=["xlsx", "csv"],
            help="Upload file with identifier columns to filter by"
        )

    if main_file and filter_file:
        try:
            # Read files with string preservation
            def read_file_with_strings(file):
                if file.name.endswith('.xlsx'):
                    return pd.read_excel(file, dtype=str)
                return pd.read_csv(file, dtype=str)

            main_df = read_file_with_strings(main_file)
            filter_df = read_file_with_strings(filter_file)

            # Clean data while preserving types
            def clean_string_series(series):
                return series.str.strip() if series.dtype == 'object' else series

            main_df = main_df.apply(clean_string_series)
            filter_df = filter_df.apply(clean_string_series)

            # Validate columns based on mode
            errors = []
            if filter_mode == "Filter by SKU":
                filter_columns = filter_df.columns.tolist()
                missing_columns = [col for col in filter_columns if col not in main_df.columns]
                if missing_columns:
                    errors.append(f"Missing columns in main file: {', '.join(missing_columns)}")
            else:
                if 'Family Id' not in main_df.columns:
                    errors.append("'Family Id' column missing in main file")
                
                # Let user select identifier column for family lookup
                identifier_column = st.selectbox(
                    "Select Identifier Column in Filter File:",
                    options=filter_df.columns,
                    help="Select column containing identifiers to find family members"
                )
                
                if identifier_column not in main_df.columns:
                    errors.append(f"'{identifier_column}' column missing in main file")

            if errors:
                st.error("Validation Errors:")
                for error in errors:
                    st.write(f"- {error}")
                return

            # Process data based on filter mode
            if filter_mode == "Filter by SKU":
                # Original SKU filtering logic
                filter_values = {}
                for col in filter_df.columns:
                    clean_values = filter_df[col].dropna().astype(str).str.strip().unique()
                    if clean_values.any():
                        filter_values[col] = set(clean_values)

                mask = pd.Series(False, index=main_df.index)
                for col, values in filter_values.items():
                    main_df[col] = main_df[col].astype(str).str.strip()
                    mask |= main_df[col].isin(values)
                
                filtered_df = main_df[mask].copy()

            else:  # Filter by Family
                # Get unique identifiers from filter file
                filter_ids = filter_df[identifier_column].dropna().astype(str).str.strip().unique()
                
                # Find matching family IDs in main data
                family_mask = main_df[identifier_column].astype(str).str.strip().isin(filter_ids)
                family_ids = main_df[family_mask]['Family Id'].astype(str).str.strip().unique()
                
                # Filter by family IDs
                filtered_df = main_df[main_df['Family Id'].astype(str).str.strip().isin(family_ids)].copy()

            # Show statistics
            st.success(f"Found {len(filtered_df)} matching records")

            # Preview
            with st.expander("Preview Filtered Data", expanded=False):
                st.dataframe(
                    filtered_df,
                    height=400,
                    use_container_width=True
                )

            # Export
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Filtered Records')
                
                # Auto-format columns
                worksheet = writer.sheets['Filtered Records']
                text_format = writer.book.add_format({'num_format': '@'})
                
                for idx, col in enumerate(filtered_df.columns):
                    max_len = max(
                        filtered_df[col].astype(str).str.len().max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(
                        idx, idx, 
                        min(max_len, 50),
                        cell_format=text_format
                    )
                
                worksheet.autofilter(0, 0, len(filtered_df), len(filtered_df.columns)-1)

            st.download_button(
                "Download Filtered Results",
                data=output.getvalue(),
                file_name="filtered_records.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Processing failed: {str(e)}")

if __name__ == "__main__":
    run()