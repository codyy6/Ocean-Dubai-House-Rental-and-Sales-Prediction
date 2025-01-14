import streamlit as st
import pymongo
import certifi

# MongoDB connection setup
ca = certifi.where()
MONGO_URI = st.secrets["mongo"]["host"]

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(MONGO_URI, tlsCAFile=ca)

def config():
    st.set_page_config(
        page_title="OceanDubai | Home",
        page_icon="🏠",
        layout="wide"
    )
    st.markdown("""
        <style>
        /* Hero section styles */
        .hero-section {
            padding: 2rem;
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1512453979798-5ea266f8880c');
            background-size: cover;
            color: white;
            text-align: center;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    config()
    
    # Hero Section
    st.markdown("""
        <div class="hero-section">
            <h1>🌊 Welcome to OceanDubai 🏖️</h1>
            <p>✨ Your Advanced Real Estate Price Prediction Platform ✨</p>
        </div>
    """, unsafe_allow_html=True)
    
    # About Section
    st.header("📖 About OceanDubai")
    st.write("""
    OceanDubai is a cutting-edge platform that leverages machine learning to predict 
    property rental and sale prices in Dubai's dynamic real estate market. Our platform 
    provides accurate insights for investors, real estate professionals, and homebuyers.
    """)
    
    # Features Section
    st.header("🎯 Key Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🏢 Property Analysis
        - 📊 Detailed property insights
        - 📈 Historical price trends
        - 📍 Location-based analytics
        """)
        
    with col2:
        st.markdown("""
        ### Price Prediction
        - Machine learning models
        - Real-time market data
        - Accurate forecasting
        """)
        
    with col3:
        st.markdown("""
        ### Market Intelligence
        - Market trends
        - Investment opportunities
        - Economic indicators
        """)
    
    # How It Works
    st.header("How It Works")
    st.write("""
    1. Input property details
    2. Get instant price predictions
    3. View detailed market analysis
    4. Make informed decisions
    """)
    
    # Connect to MongoDB and display any relevant data
    try:
        client = init_connection()
        if client:
            st.success("Connected to database successfully!")
    except Exception as e:
        st.error(f"Database connection error: {e}")

if __name__ == "__main__":
    main()
