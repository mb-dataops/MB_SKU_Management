# SKU_Maintenance.py
import streamlit as st
from modules.visibility import run as run_visibility
from modules.retirement import run as run_retirement
from modules.primarychild import run as run_primarychange
from modules.filterRecord import run as run_filter
# from modules.reenable import run as run_reenable

def main():
    # CSS injection for clean UI
    st.markdown("""
    <style>
        [data-testid="stDecoration"], [data-testid="stHeader"], #MainMenu {
            display: none;
        }
        .stApp {
            margin-top: -75px;
        }
        .sidebar .sidebar-content {
            background-color: #111;
            color: white;
        }
        .stButton>button {
            width: 100%;
            justify-content: center;
        }
    </style>
    """, unsafe_allow_html=True)

    # Navigation Header
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("← Back to Home"):
            st.session_state.page = 'home'
            st.rerun()

    st.title("SKU Maintenance Console")

    # Sidebar navigation
    with st.sidebar:
        
        # Wrap content in a centered container
        st.markdown("""
        <div class="sidebar-centered-container">
            <div class="sidebar-content">
                <h2 style='text-align: center; margin-bottom: 30px;'>Navigation</h2>
        """, unsafe_allow_html=True)
        nav_choice = st.radio(
            "Select Section:",
            options=["Visibility", "SKU Retirement", "Re-enable SKUs", "Change Primary Child", "Filter Records"],
            index=0
        )
        st.markdown("""
            <div style='margin: 30px 0;'>
                <hr style='border-color: #666;'>
            </div>
        """, unsafe_allow_html=True)
        
        
    # Main content routing
    st.divider()
    
    if nav_choice == "Visibility":
        st.subheader("Visibility Section")
        run_visibility()
    elif nav_choice == "SKU Retirement":
        st.subheader("SKU Retirement Section")
        run_retirement()
    elif nav_choice == "Re-enable SKUs":
        st.info('Currently under work', icon="ℹ️")
    elif nav_choice == "Change Primary Child":
        st.subheader("Primary Child Updating Template")
        run_primarychange()
    elif nav_choice == "Filter Records":
        st.subheader("Raw Record Filtering")
        run_filter()
    
if __name__ == "__main__":
    main()