import streamlit as st
import folium
from streamlit_folium import st_folium
import os

import pymongo
import certifi

import requests
from requests.structures import CaseInsensitiveDict


# MongoDB connection setup
ca = certifi.where()
MONGO_URI = st.secrets["mongo"]["host"]

GEOAPIFY = st.secrets["geoapify"]["key"]

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(MONGO_URI, tlsCAFile=ca)

dirname = os.path.dirname(__file__)

def config():
    st.set_page_config(
        layout="wide",
        page_title="OceanDubai | AI Property Prediction",
        page_icon="🏡"
    )
    st.title("AI Property Prediction 🏡 ✨")
    
    # Custom CSS (unchanged)
    st.markdown("""
        <style>
        .metric-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        .prediction-card {
            background-color: #00c2af;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)

def render_property_predictor():
    """Render property prediction interface"""
    
    url = "https://api.geoapify.com/v1/geocode/search?text=38%20Upper%20Montagu%20Street%2C%20Westminster%20W1H%201LJ%2C%20United%20Kingdom&apiKey=" + GEOAPIFY

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    resp = requests.get(url, headers=headers)

    print(resp.status_code)
    
    # Create tabs for different prediction types
    tab1, tab2 = st.tabs(["🎯 Basic Prediction", "🎲 Advanced Prediction"])
    
    with tab1:
        st.subheader("🏠 Basic Property Prediction")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Property Details")
            property_type = st.selectbox("🏢 Property Type", [
                "Apartment", "Villa", "Townhouse", "Penthouse"
            ])
            rooms = st.number_input("🛏️ Number of Bedrooms", 0, 10, 2)
            property_size = st.number_input("📏 Property Size (sq.m)", 30.0, 1000.0, 100.0)
            area = st.selectbox("📍 Area/Neighborhood", [
                "Dubai Marina", "Downtown Dubai", "Palm Jumeirah", "JBR"
            ])
        
        with col2:
            st.markdown("### 🗺️ Location Details")
            nearest_metro = st.selectbox("🚇 Nearest Metro", [
                "Dubai Marina", "Mall of the Emirates", "Burj Khalifa/Dubai Mall"
            ])
            nearest_mall = st.selectbox("🛍️ Nearest Mall", [
                "Dubai Mall", "Mall of the Emirates", "Marina Mall"
            ])
            nearest_landmark = st.selectbox("🏛️ Nearest Landmark", [
                "Burj Khalifa", "Burj Al Arab", "Palm Jumeirah"
            ])
            usage = st.selectbox("🏗️ Usage", ["Residential", "Commercial"])

        # Map for location selection
        st.subheader("📍 Select Property Location")
        m = folium.Map(location=[25.2048, 55.2708], zoom_start=11)
        st_folium(m, height=400, width=None)
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("💰 Predict Sale Price"):
                with st.spinner("🔄 Calculating sale price..."):
                    st.markdown("""
                        <div class="prediction-card">
                            <h3>💎 Predicted Sale Price</h3>
                            <h2>AED 1,500,000</h2>
                            <p>🎯 Confidence Score: 85%</p>
                        </div>
                    """, unsafe_allow_html=True)
        
        with col4:
            if st.button("🏦 Predict Rental Price"):
                with st.spinner("🔄 Calculating rental price..."):
                    st.markdown("""
                        <div class="prediction-card">
                            <h3>💫 Predicted Monthly Rent</h3>
                            <h2>AED 8,500</h2>
                            <p>🎯 Confidence Score: 88%</p>
                        </div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.subheader("🎲 Advanced Property Prediction")
        col5, col6 = st.columns(2)
        
        with col5:
            st.markdown("### 📊 Market Analysis")
            st.number_input("📈 Previous Month Average Price (AED)", 0.0, 10000000.0, 1000000.0)
            st.number_input("📉 Previous Week Average Price (AED)", 0.0, 10000000.0, 1000000.0)
            st.selectbox("🏗️ Property Condition", ["Excellent", "Good", "Fair", "Needs Renovation"])
            
        with col6:
            st.markdown("### 🏠 Property Features")
            st.number_input("⏳ Years Since Construction", 0, 50, 5)
            st.selectbox("👀 View Type", ["Sea View", "City View", "Garden View", "No View"])
            st.selectbox("🛋️ Furnishing Status", ["Fully Furnished", "Semi-Furnished", "Unfurnished"])

        if st.button("🎯 Run Advanced Prediction"):
            col7, col8 = st.columns(2)
            with col7:
                st.markdown("""
                    <div class="prediction-card">
                        <h3>💎 Advanced Sale Price Prediction</h3>
                        <h2>AED 1,650,000</h2>
                        <p>🎯 Confidence Score: 92%</p>
                        <p>📊 RMSE: 45000</p>
                        <p>📈 R²: 0.89</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col8:
                st.markdown("""
                    <div class="prediction-card">
                        <h3>💫 Advanced Rental Price Prediction</h3>
                        <h2>AED 9,200</h2>
                        <p>🎯 Confidence Score: 94%</p>
                        <p>📊 RMSE: 500</p>
                        <p>📈 R²: 0.91</p>
                    </div>
                """, unsafe_allow_html=True)

def main():
    config()
    render_property_predictor()

if __name__ == "__main__":
    main()
