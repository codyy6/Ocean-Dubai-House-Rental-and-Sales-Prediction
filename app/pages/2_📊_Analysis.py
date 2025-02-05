import streamlit as st
import pandas as pd

import pymongo
import certifi

from streamlit_echarts import st_echarts
import folium
from streamlit_folium import st_folium, folium_static

import requests
from requests.structures import CaseInsensitiveDict

import os
from mistralai import Mistral


# MongoDB connection setup
ca = certifi.where()
MONGO_URI = st.secrets["mongo"]["host"]

GEOAPIFY = st.secrets["geoapify"]["key"]

MISTRAL_API_KEY = st.secrets["mistral"]["key"]
MODEL = "mistral-large-latest"
client = Mistral(api_key=MISTRAL_API_KEY)

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(MONGO_URI, tlsCAFile=ca, maxPoolSize=5)

@st.cache_data(ttl=3600)
def fetch_data(collection_name):
    """Fetch data from MongoDB with connection pooling"""
    try:
        client = init_connection()
        db = client.tourism_db
        return pd.DataFrame(list(db[collection_name].find()))
    except Exception as e:
        st.error(f"Error fetching {collection_name}: {str(e)}")
        return pd.DataFrame()

def mistral_analysis(prompt, data):
    """Generate investment insights using Mistral AI"""
    try:
        # Calculate metrics
        metrics = calculate_market_metrics(data)
        
        # Create analysis message
        messages = [
            {
                "role": "system",
                "content": "You are a real estate market analysis expert. Analyze the data and provide detailed insights. Add necessary emoji to make conversation looks more fun to read"
            },
            {
                "role": "user",
                "content": f"""
                Based on the provided real estate market data:
                
                {prompt}
                
                Key metrics:
                {metrics}
                
                Provide a detailed analysis structured in sections according to the prompt
                """
            }
        ]
        
        # Generate analysis
        response = client.chat.complete(
            model=MODEL,
            messages=messages
        )
        
        st.write(response.choices[0].message.content)
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error in AI analysis: {str(e)}"

def calculate_market_metrics(data):
    """Calculate key market metrics from datasets"""
    metrics = []
    
    for name, df in data.items():
        if name == "Rental Market":
            metrics.append(f"Average Rent: {df['Contract Amount'].mean():,.0f} AED")
            metrics.append(f"Rental Volume: {len(df):,} transactions")
            
        elif name == "GDP Growth":
            metrics.append(f"GDP Growth Rate: {df['Value'].mean():.1f}%")
            
        elif name == "Property Transactions":
            metrics.append(f"Transaction Volume: {len(df):,}")
            metrics.append(f"Average Transaction Value: {df['Amount'].mean():,.0f} AED")
    
    return "\n".join(metrics)

def generate_market_insights(data, start_date, end_date):
    """Generate structured market insights using Mistral"""
    prompt = f"""
    Analyze Dubai real estate market data ({start_date} to {end_date}):
    1. Current market phase and trends
    2. Investment opportunities by area/type
    """
    
    try:
        analysis = mistral_analysis(prompt, data)
        return {
            'market_analysis': extract_section(analysis, 'Market Analysis'),
            'opportunities': extract_section(analysis, 'Opportunities'),
            'risks': extract_section(analysis, 'Risks')
        }
    except Exception as e:
        return {
            'market_analysis': f"Analysis error: {str(e)}",
            'opportunities': "Unable to generate opportunities",
            'risks': "Unable to assess risks"
        }

def generate_risk_strategies(data):
    """Generate risk management strategies using Mistral"""
    prompt = "Analyze market risks and suggest mitigation strategies, specifically only focuses on the risk factors and management"
    
    try:
        analysis = mistral_analysis(prompt, data)
        return parse_risk_analysis(analysis)
    except Exception as e:
        return default_risk_strategies()

def filter_dataset_by_date(df, start_date, end_date):
    """Filter dataset by date range with proper date format handling"""
    try:
        df = df.copy()
        
        if 'Quarter' in df.columns:
            def parse_quarter(q):
                try:
                    if pd.isna(q):
                        return pd.NaT
                        
                    q = str(q).strip()
                    
                    # Handle "2023Q3" format
                    if len(q) == 6 and q[4] == 'Q':
                        year = int(q[:4])
                        quarter = int(q[5])
                    # Handle "Q3-2023" format    
                    elif q.startswith('Q') and '-' in q:
                        parts = q.split('-')
                        quarter = int(parts[0][1])
                        year = int(parts[1])
                    else:
                        return pd.NaT
                    
                    if not (1 <= quarter <= 4):
                        return pd.NaT
                        
                    month = ((quarter - 1) * 3) + 1
                    return pd.Timestamp(f"{year}-{month:02d}-01")
                    
                except (ValueError, IndexError, TypeError):
                    return pd.NaT

            # Convert quarters to dates
            df['Quarter'] = df['Quarter'].apply(parse_quarter)
            date_col = 'Quarter'
            
        elif 'Time Period' in df.columns:
            date_col = 'Time Period'
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        else:
            return df

        # Clean data
        df = df.dropna(subset=[date_col])
            
        # Filter by date range
        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        return df[df[date_col].between(start_ts, end_ts)]
        
    except Exception as e:
        st.error(f"Error filtering data: {str(e)}")
        return df

def default_risk_strategies():
    """Default risk strategies when analysis fails"""
    return {
        'strategies': [
            {
                'name': 'Market Volatility',
                'description': 'Monitor price fluctuations and transaction volumes',
                'confidence': 0.7
            },
            {
                'name': 'Economic Factors',
                'description': 'Track GDP, inflation, and interest rates',
                'confidence': 0.8
            },
            {
                'name': 'Regulatory Changes',
                'description': 'Stay informed about property laws and regulations',
                'confidence': 0.6
            }
        ],
        'metrics': [
            {
                'label': 'Risk Score',
                'value': '3.5/5',
                'delta': '-0.2'
            },
            {
                'label': 'Market Stability',
                'value': '85%',
                'delta': '+5%'
            }
        ]
    }

def parse_risk_analysis(analysis_text):
    """Parse Mistral analysis into structured risk data"""
    try:
        risk_data = {
            'strategies': [],
            'metrics': []
        }
        
        # Extract strategies
        strategy_sections = analysis_text.split('\n\n')
        for section in strategy_sections[:3]:
            if section.strip():
                name = section.split(':')[0].strip()
                desc = section.split(':')[1].strip() if ':' in section else section
                # Normalize confidence score between 0 and 1
                confidence = min(max(round(0.5 + len(desc) / 200, 2), 0), 1)
                risk_data['strategies'].append({
                    'name': name,
                    'description': desc,
                    'confidence': confidence
                })
        
        # Add default metrics if none found
        if not risk_data['metrics']:
            risk_data['metrics'] = default_risk_strategies()['metrics']
            
        return risk_data
    except Exception as e:
        st.error(f"Error parsing risk analysis: {str(e)}")
        return default_risk_strategies()

def config():    
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

def parse_quarter(q_str):
    year = int(q_str[:4])
    quarter = int(q_str[-1])
    return pd.Period(year=year, quarter=quarter, freq='Q')

def prepare_chart_data(df):
    """Clean and prepare data for charts"""
    return [float(x) if pd.notnull(x) else None for x in df]

def get_coordinates(address):
    url = f"https://api.geoapify.com/v1/geocode/search?text={address}, Dubai, UAE&apiKey={GEOAPIFY}"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"

    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if data['features']:
            lat = data['features'][0]['properties']['lat']
            lon = data['features'][0]['properties']['lon']
            return lat, lon
    return 0, 0
    
def market_overview_tab():
    # Fetch data from MongoDB collections
    hotel_ratings = fetch_data("hotel_establishments_and_rooms_by_rating_type")
    guests_data = fetch_data("guests_by_hotel_type_by_region")
    revenue_data = fetch_data("hotel_establishments_main_indicators")
    rental_data = fetch_data("rents_quarterly")
    transactions_data = fetch_data("transactions_df_quarterly_data")
    
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
        
        # Rental Analysis
        st.markdown("""
            <h4>🏢 Rental Trends Analysis</h4>
        """, unsafe_allow_html=True)

        # Convert relevant columns to numeric
        rental_data['Contract Amount'] = pd.to_numeric(rental_data['Contract Amount'], errors='coerce')
        rental_data['Property Size (sq.m)'] = pd.to_numeric(rental_data['Property Size (sq.m)'], errors='coerce')

        # Parse and sort quarters
        rental_data['Quarter'] = rental_data['Quarter'].apply(parse_quarter)
        rental_data = rental_data.sort_values('Quarter')

        # Rental trends over time
        quarterly_rentals = rental_data.groupby('Quarter')['Contract Amount'].agg(['mean', 'count']).reset_index()
        formatted_quarters = quarterly_rentals['Quarter'].dt.strftime('%Y-Q%q').tolist()

        rental_trend_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Average Rent", "Number of Contracts"]},
            "xAxis": {
                "type": "category", 
                "data": formatted_quarters,
                "axisLabel": {"rotate": 45}
            },
            "yAxis": [
                {"type": "value", "name": "Average Rent (AED)"}, 
                {"type": "value", "name": "Number of Contracts"}
            ],
            "series": [
                {
                    "name": "Average Rent",
                    "data": quarterly_rentals['mean'].round(2).tolist(),
                    "type": "line",
                    "smooth": True
                },
                {
                    "name": "Number of Contracts", 
                    "data": quarterly_rentals['count'].tolist(),
                    "type": "bar",
                    "yAxisIndex": 1
                }
            ],
            "dataZoom": [{"type": "slider"}],
            "grid": {"bottom": "15%"}
        }
        st_echarts(rental_trend_chart)

        # Property type distribution
        st.markdown("<h5>Property Type Distribution</h5>", unsafe_allow_html=True)
        property_dist = rental_data['Property Type'].value_counts()
        
        property_pie = {
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "horizontal", "bottom": "bottom"},
            "series": [{
            "type": "pie",
            "data": [{"value": v, "name": k} for k,v in property_dist.items()],
            "radius": "50%"
            }]
        }
        st_echarts(property_pie)

        # Area-wise average rent 
        st.markdown("<h5>Average Rent by Area</h5>", unsafe_allow_html=True)
        area_rent = rental_data.groupby('Area')['Contract Amount'].mean().sort_values(ascending=False)

        area_bar = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {
            "type": "category",
            "data": area_rent.index.tolist()[:10],
            "axisLabel": {"rotate": 45}
            },
            "yAxis": {"type": "value"},
            "series": [{
            "data": area_rent.values.round(2).tolist()[:10],
            "type": "bar",
            "name": "Average Rent"
            }]
        }
        st_echarts(area_bar)

    
    with col2:
        st.markdown("""
            <h4>💰 Guest Nights & Room Revenue Trends</h4>
        """, unsafe_allow_html=True)
        
        # Process revenue data
        guest_nights = revenue_data[revenue_data['Hotel Indicator'] == 'Guest Nights'].sort_values('Time Period')
        room_revenue = revenue_data[revenue_data['Hotel Indicator'] == 'Room Revenue'].sort_values('Time Period')
        
        # Create DataFrame with aligned time periods
        merged_data = pd.merge(
            guest_nights[['Time Period', 'Value']].rename(columns={'Value': 'Guest Nights'}),
            room_revenue[['Time Period', 'Value']].rename(columns={'Value': 'Room Revenue'}),
            on='Time Period',
            how='inner'
        )
        
        revenue_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Guest Nights", "Room Revenue"]},
            "xAxis": {"type": "category", "data": merged_data['Time Period'].tolist()},
            "yAxis": [
            {"type": "value", "name": "Guest Nights"},
            {"type": "value", "name": "Room Revenue (AED)"}
            ],
            "series": [
            {
                "name": "Guest Nights",
                "data": merged_data['Guest Nights'].tolist(),
                "type": "line",
                "smooth": True
            },
            {
                "name": "Room Revenue",
                "data": merged_data['Room Revenue'].tolist(),
                "type": "line", 
                "smooth": True,
                "yAxisIndex": 1
            }
            ],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(revenue_chart)
        
        st.markdown("""
            <h4>🏠 Property Transaction Analysis</h4>
        """, unsafe_allow_html=True)

        # Convert and sort quarters
        transactions_data['Quarter'] = transactions_data['Quarter'].apply(parse_quarter)
        transactions_data = transactions_data.sort_values('Quarter')

        # Format quarters for display
        formatted_quarters = transactions_data['Quarter'].dt.strftime('%Y-Q%q').tolist()

        transactions_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Transaction Amount", "Transaction Size"]},
            "xAxis": {
                "type": "category", 
                "data": formatted_quarters,
                "axisLabel": {
                    "rotate": 45
                }
            },
            "yAxis": [
                {"type": "value", "name": "Amount (AED)"},
                {"type": "value", "name": "Size (sq.m)"}
            ],
            "series": [
                {
                    "name": "Transaction Amount",
                    "type": "line",
                    "data": transactions_data['Amount'].tolist(),
                    "smooth": True
                },
                {
                    "name": "Transaction Size",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": transactions_data['Transaction Size (sq.m)'].tolist(),
                    "smooth": True
                }
            ],
            "dataZoom": [{"type": "slider"}],
            "grid": {
                "bottom": "15%"
            }
        }
        st_echarts(transactions_chart)

        # Scatter plot of amount vs size
        st.markdown("""
            <h4>📈 Transaction Size vs Amount</h4>
        """, unsafe_allow_html=True)
        
        scatter_chart = {
            "tooltip": {"trigger": "item"},
            "xAxis": {"type": "value", "name": "Transaction Size (sq.m)"},
            "yAxis": {"type": "value", "name": "Amount (AED)"},
            "series": [{
            "type": "scatter",
            "data": [[size, amount] for size, amount in zip(
            transactions_data['Transaction Size (sq.m)'].tolist(),
            transactions_data['Amount'].tolist()
            )],
            "symbolSize": 10
            }]
        }
        st_echarts(scatter_chart)
        
        
        # Create a base map centered on Dubai
        def create_map():
            # Create a base map centered on Dubai
            m = folium.Map(location=[25.2048, 55.2708], zoom_start=6)

            # Filter out rows with missing coordinates and get unique lat/long combinations
            valid_data = rental_data[
                rental_data['Latitude'].notna() & 
                rental_data['Longitude'].notna()
            ].drop_duplicates(subset=['Latitude', 'Longitude'])

            # Create markers for each unique location
            for _, row in valid_data.iterrows():
                popup_html = f"""
                <b>Area:</b> {row['Area']}<br>
                <b>Property Type:</b> {row['Property Type']}<br>
                <b>Property Sub Type:</b> {row['Property Sub Type']}<br>
                <b>Usage:</b> {row['Usage']}<br>
                <b>Contract Amount:</b> {row['Contract Amount']:,.0f} AED<br>
                <b>Nearest Metro:</b> {row['Nearest Metro']}<br>
                <b>Nearest Mall:</b> {row['Nearest Mall']}<br>
                <b>Nearest Landmark:</b> {row['Nearest Landmark']}
                """
                
                folium.Marker(
                    [row['Latitude'], row['Longitude']], 
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=row['Area']
                ).add_to(m)
            
            heat_data = valid_data[['Latitude', 'Longitude']].values.tolist()
            folium.plugins.HeatMap(heat_data).add_to(m)
            
            return m

        # Display the map
        m = create_map()
        # Add heatmap
        st.markdown("<h4>📍 Property Density Heatmap</h4>", unsafe_allow_html=True)
        folium_static(m, width=700, height=500)


def macroeconomic_tab():
    aed_to_usd =fetch_data("aed_to_usd_df")
    gdp_data =fetch_data("gdp_quarterly_current_prices_df")
    population_data = fetch_data("population_indicators_df")
    cpi_data = data = fetch_data("consumer_price_index_monthly_df")
    wdi_data = data = fetch_data("world_development_indicator_df")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <h4>💵 AED to USD</h4>
        """, unsafe_allow_html=True)

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
    # Fetch datasets
    datasets = {
        "Rental Market": fetch_data("rents_quarterly"),
        "GDP Growth": fetch_data("gdp_quarterly_current_prices_df"),
        "Consumer Price Index": fetch_data("consumer_price_index_monthly_df"),
        "Population": fetch_data("population_indicators_df"),
        "Property Transactions": fetch_data("transactions_df_quarterly_data")
    }

    # Sidebar controls
    with st.sidebar:
        st.markdown("### 📊 Analysis Configuration")
        selected_datasets = st.multiselect(
            "Select Data Sources",
            list(datasets.keys()),
            default=list(datasets.keys())[:2],
            help="Choose datasets for analysis"
        )

        # Date range selector
        st.markdown("### 📅 Time Period")
        min_date = pd.Timestamp('2015-01-01')
        max_date = pd.Timestamp('2024-12-31')
        start_date, end_date = st.date_input(
            "Analysis Period",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    # Main content columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
                <h4>🎯 Investment Opportunities</h4>
        """, unsafe_allow_html=True)

        # Prepare analysis data
        analysis_data = {
            name: filter_dataset_by_date(datasets[name], start_date, end_date)
            for name in selected_datasets
        }

        # Generate insights
        if analysis_data:
            with st.spinner("Generating market insights..."):
                insights = generate_market_insights(analysis_data, start_date, end_date)
        else:
            st.warning("Please select at least one dataset for analysis")

    with col2:
        st.markdown("""
                <h4>🛡️ Risk Management</h4>
        """, unsafe_allow_html=True)

        # Generate risk mitigation strategies
        with st.spinner("Analyzing risks..."):
            risk_analysis = generate_risk_strategies(analysis_data)
            

def correlation_tab():
    rental_data = fetch_data("rents_quarterly")
    gdp_data = fetch_data("gdp_quarterly_current_prices_df")
    cpi_data = fetch_data("consumer_price_index_monthly_df")
    population_data = fetch_data("population_indicators_df")
    
    try:
        rental_data['Quarter'] = pd.to_datetime(rental_data['Quarter'].apply(lambda x: x[:4] + '-' + str(int(x[-1]) * 3)), format='ISO8601')
        rental_data['Quarter'] = rental_data['Quarter'].dt.to_period('Q').dt.end_time

        # Create quarterly metrics
        rental_metrics = rental_data.resample('QE', on='Quarter').agg({
            'Contract Amount': 'mean',
            'Quarter': 'count'
        }).rename(columns={
            'Contract Amount': 'Average_Rent',
            'Quarter': 'Transaction_Volume'
        })

        # GDP data
        gdp_data['Time Period'] = gdp_data.apply(lambda row: pd.Timestamp(f"{int(row['Time Period'])}-{int(row['Quarter'][-1])*3}-01"), axis=1)
        
        # Group by Time Period and sum values for the same date
        gdp_data = gdp_data.groupby('Time Period', as_index=False)['Value'].sum()
        
        # Convert to quarterly data and handle duplicates
        gdp_data['Time Period'] = pd.to_datetime(gdp_data['Time Period'])
        gdp_growth = gdp_data \
            .set_index('Time Period')['Value'] \
            .resample('QE').sum() \
            .drop_duplicates() \
            .to_frame('GDP_Growth')


        # CPI data
        cpi_data['Time Period'] = pd.to_datetime(cpi_data['Time Period'])
        cpi_quarterly = cpi_data.resample('QE', on='Time Period')['Value'].mean() \
            .to_frame('CPI')

        # Population data
        population_data['Time_Period'] = pd.to_datetime(population_data['Time_Period'].astype(str) + '-01')

        # Create quarterly data with unique indices
        pop_quarterly = []
        for _, row in population_data.iterrows():
            year = row['Time_Period'].year
            for quarter in range(1, 5):
                quarter_date = pd.Timestamp(f"{year}-{3*quarter}-01")
                pop_quarterly.append({
                    'Time_Period': quarter_date,
                    'Value': row['Value']
                })

        # Convert to DataFrame and ensure unique index
        population_df = pd.DataFrame(pop_quarterly)
        population_df = population_df.drop_duplicates('Time_Period')
        population_clean = population_df.set_index('Time_Period')['Value'].to_frame('Population')

        # Sort index and handle any remaining duplicates
        population_clean = population_clean.sort_index()
        population_clean = population_clean[~population_clean.index.duplicated(keep='first')]

        # Create common index
        start_date = min(
            rental_metrics.index.min(),
            gdp_growth.index.min(),
            cpi_quarterly.index.min(),
            population_clean.index.min()
        )
        end_date = max(
            rental_metrics.index.max(),
            gdp_growth.index.max(),
            cpi_quarterly.index.max(),
            population_clean.index.max()
        )
        full_index = pd.date_range(start=start_date, end=end_date, freq='QE')

        # Reindex all dataframes with common index
        dfs = {
            'Rental': rental_metrics,
            'GDP': gdp_growth,
            'CPI': cpi_quarterly,
            'Population': population_clean
        }

        aligned_dfs = []
        for name, df in dfs.items():
            aligned = df.reindex(full_index)
            aligned.columns = [f"{name}_{col}" for col in aligned.columns]
            aligned_dfs.append(aligned)

        # Combine aligned dataframes
        correlation_df = pd.concat(aligned_dfs, axis=1)

        # Calculate correlation matrix
        corr_matrix = correlation_df.corr().round(2)
        
        st.markdown("### 📈 Time Series Analysis")
        
        rental_metrics_clean = rental_metrics.fillna(method='ffill')
        gdp_growth_clean = gdp_growth.fillna(method='ffill')
        cpi_quarterly_clean = cpi_quarterly.fillna(method='ffill')
        population_clean = population_clean.fillna(method='ffill')

        # Price vs Economic Indicators
        price_gdp_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": ["Average Rent", "GDP Growth", "CPI"]
            },
            "xAxis": {
                "type": "category",
                "data": rental_metrics_clean.index.strftime('%Y-%m').tolist()
            },
            "yAxis": [
                {"type": "value", "name": "Average Rent (AED)", "position": "left"},
                {"type": "value", "name": "Growth Rate (%)", "position": "right"}
            ],
            "series": [
                {
                    "name": "Average Rent",
                    "type": "line",
                    "data": prepare_chart_data(rental_metrics_clean['Average_Rent']),
                    "smooth": True
                },
                {
                    "name": "GDP Growth",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": prepare_chart_data(gdp_growth_clean['GDP_Growth']),
                    "smooth": True
                },
                {
                    "name": "CPI",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": prepare_chart_data(cpi_quarterly_clean['CPI']),
                    "smooth": True
                }
            ],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(price_gdp_chart)

        # Volume vs Population
        volume_pop_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {
                "data": ["Transaction Volume", "Population"]
            },
            "xAxis": {
                "type": "category",
                "data": rental_metrics_clean.index.strftime('%Y-%m').tolist()
            },
            "yAxis": [
                {"type": "value", "name": "Transactions"},
                {"type": "value", "name": "Population"}
            ],
            "series": [
                {
                    "name": "Transaction Volume",
                    "type": "bar",
                    "data": prepare_chart_data(rental_metrics_clean['Transaction_Volume'])
                },
                {
                    "name": "Population",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": prepare_chart_data(population_clean['Population']),
                    "smooth": True
                }
            ],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(volume_pop_chart)

        # Rolling Correlations
        window = 4
        rolling_corr = pd.DataFrame({
            'GDP': rental_metrics_clean['Average_Rent'].rolling(window).corr(gdp_growth_clean['GDP_Growth']),
            'CPI': rental_metrics_clean['Average_Rent'].rolling(window).corr(cpi_quarterly_clean['CPI']),
            'Population': rental_metrics_clean['Average_Rent'].rolling(window).corr(population_clean['Population'])
        })

        rolling_corr_chart = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["GDP", "CPI", "Population"]},
            "xAxis": {
                "type": "category",
                "data": rolling_corr.index.strftime('%Y-%m').tolist()
            },
            "yAxis": {"type": "value", "name": "Correlation"},
            "series": [
                {
                    "name": col,
                    "type": "line",
                    "data": prepare_chart_data(rolling_corr[col]),
                    "smooth": True
                } for col in rolling_corr.columns
            ],
            "dataZoom": [{"type": "slider"}]
        }
        st_echarts(rolling_corr_chart)
        
        col3, col4 = st.columns([2,1])
        
        with col3:
            st.markdown("<h4> 📊 Correlation Heatmap</h4>", unsafe_allow_html=True)
            
            # Generate heatmap data with proper axis labels
            heatmap_data = []
            for i, row_var in enumerate(corr_matrix.index):
                for j, col_var in enumerate(corr_matrix.columns):
                    value = corr_matrix.loc[row_var, col_var]
                    if not pd.isna(value):
                        heatmap_data.append([j, i, float(value)])  # Note j comes first for x-axis

            heatmap = {
                "tooltip": {"trigger": "item"},
                "visualMap": {
                    "min": -1,
                    "max": 1,
                    "calculable": True,
                    "orient": 'horizontal',
                    "left": 'center',
                    "bottom": '12%',
                    "inRange": {"color": ['#313695', '#4575b4', '#74add1', '#abd9e9', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']}
                },
                "xAxis": {
                    "type": "category",
                    "data": corr_matrix.columns.tolist(),
                    "axisLabel": {
                        "rotate": 45,
                        "interval": 0,
                        "fontSize": 10
                    }
                },
                "yAxis": {
                    "type": "category",
                    "data": corr_matrix.index.tolist(),
                    "axisLabel": {
                        "rotate": 0,
                        "fontSize": 10
                    }
                },
                "series": [{
                    "type": "heatmap",
                    "data": heatmap_data,
                    "label": {"show": True, "fontSize": 10},
                    "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": 'rgba(0,0,0,0.5)'}}
                }],
                "grid": {
                    "top": "15%",
                    "bottom": "25%",
                    "left": "20%",
                    "right": "5%"
                }
            }
            
            st_echarts(heatmap, height="600px")
            
            
        with col4:
            st.markdown("<h4> 📈 Data Coverage</h4>", unsafe_allow_html=True)
            st.write(f"Time period: {correlation_df.index.min()} to {correlation_df.index.max()}")
            st.write(f"Number of quarters: {len(correlation_df)}")
            st.write("Data completeness:")
            for col in correlation_df.columns:
                pct_complete = (correlation_df[col].notna().sum() / len(correlation_df) * 100).round(1)
                st.write(f"{col}: {pct_complete}%")
        
        
            st.markdown("#### 🔍 Key Insights")
            
            valid_correlations = [
                {
                    'factor1': col1,  
                    'factor2': col2,
                    'correlation': float(corr_matrix.loc[col1, col2])
                }
                for col1 in corr_matrix.columns
                for col2 in corr_matrix.columns 
                if col1 < col2 and not pd.isna(corr_matrix.loc[col1, col2])
            ]
            
            valid_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            for corr in valid_correlations[:5]:
                with st.container():
                    container_content = st.container()
                    container_content.write(f"{corr['factor1']} vs {corr['factor2']}")
                    strength = 'Strong' if abs(corr['correlation']) > 0.7 else 'Moderate'
                    direction = 'positive' if corr['correlation'] > 0 else 'negative'
                    container_content.write(f"{strength} {direction} correlation: {corr['correlation']:.2f}")
                st.divider()
                
    except Exception as e:
        st.error(f"Error in correlation analysis: {str(e)}")
        st.write("Please check data integrity and time period alignment")


def render_view():
    # Create tabs
    st.subheader("🏘️ Market Overview")
    market_overview_tab()
    
    st.subheader("🌍 Macroeconomic Factors")
    macroeconomic_tab()
    
    st.subheader("⫻ Correlation")
    correlation_tab()
    
    st.subheader("💡 Investment Insights")
    investment_tab()
    
if __name__ == "__main__":
    config()
    render_view()
