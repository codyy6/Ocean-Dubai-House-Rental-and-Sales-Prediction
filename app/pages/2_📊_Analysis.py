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
    
    with col2:
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



def macroeconomic_tab():
    # Initialize MongoDB connections
    tourism_db = client.tourism_db
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <h4>💵 AED to USD</h4>
        """, unsafe_allow_html=True)

        aed_to_usd = pd.DataFrame(list(tourism_db.aed_to_usd_df.find()))
        gdp_data = pd.DataFrame(list(tourism_db.gdp_quarterly_current_prices_df.find()))

        # Process AED to USD data
        aed_to_usd = aed_to_usd.sort_values('Date')
        exchange_chart = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": aed_to_usd['Date'].tolist()},
            "yAxis": {
            "type": "value", 
            "name": "Exchange Rate",
            "min": aed_to_usd['Close'].min() * 0.99,  # Set min slightly below lowest value
            "max": aed_to_usd['Close'].max() * 1.01   # Set max slightly above highest value
            },
            "series": [{
            "data": aed_to_usd['Close'].tolist(),
            "type": "line",
            "smooth": True,
            "name": "AED to USD",
            "lineStyle": {"width": 2},  # Make line thicker
            "markPoint": {
                "data": [
                {"type": "max", "name": "Maximum"},
                {"type": "min", "name": "Minimum"}
                ]
            }
            }],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(exchange_chart)

        # Process GDP data
        # Process GDP data
        st.markdown("""
            <h4>📈 GDP Growth Rates</h4>
        """, unsafe_allow_html=True)
        
        # Group and pivot GDP data by Measure
        gdp_measures = gdp_data.groupby(['Time Period', 'Measure'])['Value'].mean().unstack()
        
        # Add measure selection
        available_measures = gdp_measures.columns.tolist()
        # Add measure selection with a more descriptive label and help text
        col_gdp, col_gdp_all = st.columns([3,1])
        with col_gdp_all:
            if st.button('Select All GDP'):
                selected_measures = available_measures
                with col_gdp:
                    selected_measures = st.multiselect(
                    'Choose GDP Growth Rate Indicators',
                    selected_measures,
                    default=selected_measures,
                    help="Select one or more GDP measures to visualize their trends over time. Multiple selections will allow you to compare different growth rates."
                    )
            else:
                with col_gdp:
                    selected_measures = st.multiselect(
                    'Choose GDP Growth Rate Indicators',
                    available_measures,
                    default=available_measures[:3],
                    help="Select one or more GDP measures to visualize their trends over time. Multiple selections will allow you to compare different growth rates."
                    )
        if selected_measures:
            gdp_chart = {
            "tooltip": {"trigger": "axis"},
            # "legend": {"data": selected_measures},
            "xAxis": {"type": "category", "data": gdp_measures.index.astype(str).tolist()},
            "yAxis": {"type": "value", "name": "Growth Rate (%)"},
            "series": [
            {
                "name": measure,
                "data": gdp_measures[measure].tolist(),
                "type": "line",
                "smooth": True
            } for measure in selected_measures
            ],
            "dataZoom": [{"type": "slider"}]
            }
            st_echarts(gdp_chart)
        else:
            st.warning("Please select at least one measure to display")

    
    with col2:
        population_data = pd.DataFrame(list(tourism_db.population_indicators_df.find()))
        
        st.markdown("""
            <h4>👥 Population Indicators</h4>
        """, unsafe_allow_html=True)

        population_data = population_data.sort_values('Time_Period')
        pop_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Population Indicators"]},
            "xAxis": {"type": "category", "data": population_data['Time_Period'].astype(str).tolist()},
            "yAxis": {"type": "value", "name": "Value"},
            "series": [{
                "name": "Population Indicators",
                "data": population_data['Value'].tolist(),
                "type": "line",
                "smooth": True,
                "markPoint": {
                    "data": [
                        {"type": "max", "name": "Max"},
                        {"type": "min", "name": "Min"}
                    ]
                }
            }],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(pop_chart)
            
        # Fetch CPI and World Development Indicator data
        cpi_data = pd.DataFrame(list(tourism_db.consumer_price_index_monthly_df.find()))
        wdi_data = pd.DataFrame(list(tourism_db.world_development_indicator_df.find()))

        # Process CPI data
        st.markdown("<h4>📊 Consumer Price Index by Category</h4>", unsafe_allow_html=True)
        cpi_pivot = cpi_data.pivot_table(
            values='Value',
            index='Time Period',
            columns='CPI Division',
            aggfunc='mean'
        ).reset_index()
        
        # Replace NaN values with None
        cpi_pivot = cpi_pivot.where(pd.notnull(cpi_pivot), None)

        cpi_divisions = cpi_data['CPI Division'].unique().tolist()
        col_select, col_select_all = st.columns([3,1])
        with col_select_all:
            if st.button('Select All'):
                selected_divisions = cpi_divisions
                with col_select:
                    st.multiselect(
                        'Select CPI divisions to display',
                        cpi_divisions,
                        default=selected_divisions
                    )
            else:
                with col_select:
                    selected_divisions = st.multiselect(
                        'Select CPI divisions to display',
                        cpi_divisions,
                        default=cpi_divisions[:3]
                    )

        if selected_divisions:
            cpi_chart = {
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": cpi_pivot['Time Period'].tolist()},
                "yAxis": {"type": "value", "name": "CPI Value"},
                "series": [
                    {
                        "name": division,
                        "type": "line",
                        "smooth": True,
                        "data": [None if pd.isna(x) else x for x in cpi_pivot[division].tolist()]
                    } for division in selected_divisions
                ],
                "dataZoom": [{"type": "slider"}]
            }
            st_echarts(cpi_chart)

        # Process World Development Indicator data
        st.markdown("<h4>🌍 World Development Indicators</h4>", unsafe_allow_html=True)

        # Convert years to numeric columns
        year_columns = [str(year) for year in range(1960, 2024)]
        
        # Add indicator selection
        available_indicators = wdi_data['Indicator Name'].unique().tolist()
        selected_indicator = st.selectbox(
            'Select World Development Indicator',
            available_indicators,
            help="Choose an indicator to visualize its trend over time"
        )

        # Filter data for selected indicator
        indicator_data = wdi_data[wdi_data['Indicator Name'] == selected_indicator]
        indicator_values = [indicator_data[year].iloc[0] for year in year_columns if year in indicator_data.columns]
        valid_years = [year for year in year_columns if year in indicator_data.columns]

        indicator_chart = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": valid_years},
            "yAxis": {"type": "value", "name": selected_indicator},
            "series": [{
            "name": selected_indicator,
            "type": "line",
            "data": indicator_values,
            "smooth": True,
            "markPoint": {
                "data": [
                {"type": "max", "name": "Maximum"},
                {"type": "min", "name": "Minimum"}
                ]
            }
            }],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(indicator_chart)



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

def correlation_tab():
    """"""

def render_view():
    # Create tabs
    st.subheader("🏘️ Market Overview")
    market_overview_tab()
    
    st.subheader("🌍 Macroeconomic Factors")
    macroeconomic_tab()
    
    st.subheader("💡 Investment Insights")
    investment_tab()
    
    st.subheader("⫻ Correlation")
    correlation_tab()
if __name__ == "__main__":
    config()
    render_view()
