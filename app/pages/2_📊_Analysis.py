import streamlit as st
import pandas as pd

import pymongo
import certifi

from streamlit_echarts import st_echarts

# MongoDB connection setup
ca = certifi.where()
MONGO_URI = st.secrets["mongo"]["host"]
MONGO_URI1 = st.secrets["mongo1"]["host"]
MONGO_URI2 = st.secrets["mongo2"]["host"]

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(MONGO_URI, tlsCAFile=ca)

@st.cache_resource
def init_sec_connection():
    return pymongo.MongoClient(MONGO_URI1, tlsCAFile=ca)

@st.cache_resource
def init_third_connection():
    return pymongo.MongoClient(MONGO_URI2, tlsCAFile=ca)

client = init_connection()

def config():
    mongo_instance = init_connection()
    
    st.set_page_config(
        layout="wide",
        page_title="OceanDubai | Analysis",
        page_icon="📊"
    )
    st.title("Dubai Real Estate Market Analysis 📊 🏢 ✨")
    st.markdown("""
        <style>
        .analysis-card {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 10px 0;
            border: 1px solid #f0f2f6;
        }
        .insight-section {
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 0 24px;
            background-color: #ffffff;
            border-radius: 5px;
            border: 1px solid #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)
    
def market_overview_tab():
    # Initialize MongoDB connections
    tourism_db = client.tourism_db

    # Fetch data from MongoDB collections
    hotel_ratings = pd.DataFrame(list(tourism_db.hotel_establishments_and_rooms_by_rating_type.find()))
    guests_data = pd.DataFrame(list(tourism_db.guests_by_hotel_type_by_region.find()))
    revenue_data = pd.DataFrame(list(tourism_db.hotel_establishments_main_indicators.find()))

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
                <h4>🏨 Hotel Indicators Growth</h4>
        """, unsafe_allow_html=True)
        
        # Process hotel establishments data
        hotel_estab_data = hotel_ratings.groupby(['Time Period', 'Hotel Indicator'])['Value'].mean().unstack().reset_index()
        hotel_chart = {
            # "title": {"text": "Hotel Indicators Growth"},
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Hotel Establishments", "Rooms"]},
            "xAxis": {"type": "category", "data": hotel_estab_data['Time Period'].tolist()},
            "yAxis": [
            {"type": "value", "name": "Hotel Establishments"},
            {"type": "value", "name": "Rooms"}
            ],
            "series": [
            {
                "name": "Hotel Establishments",
                "data": hotel_estab_data['Hotel Establishments'].tolist(),
                "type": "line",
                "smooth": True
            },
            {
                "name": "Rooms",
                "data": hotel_estab_data['Rooms'].tolist(),
                "type": "line",
                "smooth": True,
                "yAxisIndex": 1
            }
            ],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(hotel_chart)
    
    with col2:
        st.write()
        
    # Sales Transactions Section
    st.subheader("🏠 Sales Market Analysis")
    
    col5, col6 = st.columns(2)
    
    with col5:
        # Guest nights chart below
        st.markdown("""
            <h4>👥 Guest Nights Analysis</h4>
        """, unsafe_allow_html=True)
        
        guest_hotels = guests_data[guests_data['Hotel Indicator'] == 'Guests - Hotels'].sort_values('Time Period')
        guest_nights = guests_data[guests_data['Hotel Indicator'] == 'Guest Nights'].sort_values('Time Period')
        guest_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Guest Nights", "Hotel Guests"]},
            "xAxis": {"type": "category", "data": guest_nights['Time Period'].tolist()},
            "yAxis": {"type": "value"},
            "series": [
                {
                    "name": "Guest Nights",
                    "data": guest_nights['Value'].tolist(),
                    "type": "bar"
                },
                {
                    "name": "Hotel Guests",
                    "data": guest_hotels['Value'].tolist(),
                    "type": "bar"
                }
            ],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(guest_chart)
        
    with col6:
        st.write()
        

    # Rental Transactions Section
    st.subheader("🏠 Rental Market Analysis")
    
    # Fetch transaction data
    # sales_data = pd.DataFrame(list(transactions_db.sales_transactions.find()))
    # rental_data = pd.DataFrame(list(transactions_db.rental_transactions.find()))

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("""
            <h4>💰 Guest Nights & Room Revenue Trends</h4>
        """, unsafe_allow_html=True)
        
        # Process revenue data
        guest_nights = revenue_data[revenue_data['Hotel Indicator'] == 'Guest Nights'].sort_values('Time Period')
        room_revenue = revenue_data[revenue_data['Hotel Indicator'] == 'Room Revenue'].sort_values('Time Period')
        
        revenue_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Guest Nights", "Room Revenue"]},
            "xAxis": {"type": "category", "data": guest_nights['Time Period'].tolist()},
            "yAxis": [
            {"type": "value", "name": "Guest Nights"},
            {"type": "value", "name": "Room Revenue (AED)"}
            ],
            "series": [
            {
                "name": "Guest Nights",
                "data": guest_nights['Value'].tolist(),
                "type": "line",
                "smooth": True
            },
            {
                "name": "Room Revenue",
                "data": room_revenue['Value'].tolist(),
                "type": "line", 
                "smooth": True,
                "yAxisIndex": 1
            }
            ],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(revenue_chart)
    

    with col4:
        st.write()
        # st.markdown("<h4>🏘️ Average Rental Price by Property Type</h4>", unsafe_allow_html=True)
        # rental_by_type = rental_data.groupby('property_type')['price'].mean().reset_index()
        # rental_chart = {
        #     "tooltip": {"trigger": "item"},
        #     "legend": {"orient": "vertical", "left": "left"},
        #     "series": [{
        #         "name": "Rental Price",
        #         "type": "pie",
        #         "radius": "50%",
        #         "data": [{"value": v, "name": k} for k, v in zip(rental_by_type['property_type'], rental_by_type['price'])]
        #     }]
        # }
        # st_echarts(rental_chart)


def macroeconomic_tab():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div class="analysis-card">
                <h3>💰 GDP Impact 📊</h3>
                [Placeholder for GDP Correlation Chart]
            </div>
        """, unsafe_allow_html=True)
        
        # tourism_db.aed_to_usd_df
        # {"_id":{"$oid":"6789f63cb2ee865657ab5275"},"Open":{"$numberDouble":"0.2723311483860016"},"High":{"$numberDouble":"0.2723682522773742"},"Low":{"$numberDouble":"0.2723311483860016"},"Close":{"$numberDouble":"0.2723682522773742"},"Adj Close":{"$numberDouble":"0.2723682522773742"},"Date":"2003-12-01","Return":{"$numberDouble":"NaN"}}
        
        # tourism_db.consumer_price_index_annually_df
        # {"_id":{"$oid":"6789f4579a3836b33c9d2d98"},"Measure":"Index number (base year 2021 = 100)","Unit of Measure":"INDX","CPI Division":"Furniture and Household Goods","Time Period":{"$numberInt":"2021"},"Value":{"$numberDouble":"100.0"}}
        
        # tourism_db.consumer_price_index_monthly_df
        # {"_id":{"$oid":"6789f4599a3836b33c9d2f09"},"Measure":"Annual Change (%)(base year 2014 = 100)","Unit of Measure":"Percentage","CPI Division":"Furniture and Household Goods","Time Period":"2009-01","Value":{"$numberDouble":"7.25"}}
        
        # tourism_db.consumer_price_index_quarterly_df
        # {"_id":{"$oid":"6789f45f9a3836b33c9d4bca"},"CPI Division":"Housing, Water, Electricity, Gas","Time Period":"2022-Q1","Value (%)":{"$numberDouble":"-1.851787981"}}
        

    
    with col2:
        st.markdown("""
            <div class="analysis-card">
                <h3>✈️ Tourism Influence 🏨</h3>
                [Placeholder for Tourism Data]
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="analysis-card">
                <h3>👥 Population Growth 📈</h3>
                [Placeholder for Population Trends]
            </div>
        """, unsafe_allow_html=True)


def investment_tab():
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class="analysis-card">
                <h3>🎯 Investment Opportunities 💫</h3>
                <ul>
                    <li>🏢 Key Investment Areas</li>
                    <li>⏰ Market Timing Indicators</li>
                    <li>⚠️ Risk Factors</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="analysis-card">
                <h3>🛡️ Risk Mitigation Strategies 📋</h3>
                <ul>
                    <li>📊 Portfolio Diversification</li>
                    <li>🔍 Market Monitoring Tools</li>
                    <li>🚪 Exit Strategies</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

def render_view():
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "🏘️ Market Overview", 
        "🌍 Macroeconomic Factors", 
        "💡 Investment Insights"
    ])
    
    with tab1:
        market_overview_tab()
    
    with tab2:
        macroeconomic_tab()
    
    with tab3:
        investment_tab()
        
if __name__ == "__main__":
    config()
    render_view()
