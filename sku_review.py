import streamlit as st
from modules.new_sku_us import run as run_us
from modules.new_sku_eu import run as run_eu
from modules.stealth_sku import run as run_stealth

def main():
    
    # CSS injection
    st.markdown("""
    <style>
        [data-testid="stDecoration"], [data-testid="stHeader"], #MainMenu {
            display: none;
        }
        .stApp {
            margin-top: -75px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation Header
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("← Back to Home"):
            st.session_state.page = 'home'
            st.rerun()
    
    st.title("SKU Review")
    
    # Selection dropdown
    sku_type = st.selectbox(
        "Select SKU Type:",
        options=["US SKUs", "EU SKUs", "Stealth SKUs"],
        index=0
    )
    
    # Display divider
    st.divider()
    
    # Module execution based on selection
    if sku_type == "US SKUs":
        run_us()
    elif sku_type == "EU SKUs":
        run_eu()
    elif sku_type == "Stealth SKUs":
        run_stealth()

if __name__ == "__main__":
    main()