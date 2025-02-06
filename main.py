import streamlit as st

def main():
    st.set_page_config(
        page_title="SKU Management Portal",
        page_icon="🏠",
        layout="centered"  # Allows better responsiveness
    )
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'

    # Navigation
    if st.session_state.page == 'home':
        show_home_page()
    elif st.session_state.page == 'sku_review':
        st.markdown("""
            <style>
                /* Hide GitHub icon */
                [data-testid="stDecoration"] {
                    display: none;
                }
                
                /* Hide header */
                [data-testid="stHeader"] {
                    display: none;
                }
                
                /* Hide menu button */
                #MainMenu {
                    visibility: hidden;
                }

            </style>
            """, unsafe_allow_html=True)
            
        import sku_review
        sku_review.main()

def show_home_page():
    st.markdown("""
    <style>
    .hero {
        padding: 2rem;
        border-radius: 12px;
        background: linear-gradient(145deg, #ecf0f3 0%, #ffffff 100%);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero h2 {
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .hero p {
        color: #7f8c8d;
        font-size: 1.1rem;
    }
    .stButton>button {
        width: 100%; /* Responsive button width */
        height: 50px;
        font-size: 1.1rem;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        background-color: #f0f0f0;
    }
    @media (max-width: 768px) {
        .stButton>button {
            font-size: 1rem;
            height: 45px;
        }
    }
    
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='hero'><h2>DataOps SKU Management Portal</h2><p>Manage SKU onboarding review and maintenance in one place</p></div>", unsafe_allow_html=True)

    # Dynamic layout for responsiveness
    cols = st.columns([1, 1, 1])  # Ensures buttons are evenly distributed

    with cols[0]:
        if st.button("🚀 Review SKU Onboarding", help="Begin new SKU onboarding process"):
            st.session_state.page = 'sku_review'
            st.rerun()

    with cols[1]:
        st.button("🛠️ SKU Maintenance (Coming Soon)", disabled=True)
        
    with cols[2]:
        st.button("🔍 Review AC Fields (Coming Soon)", disabled=True)

    

    # Footer
    st.markdown("---")

if __name__ == "__main__":
    main()
