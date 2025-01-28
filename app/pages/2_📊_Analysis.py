import streamlit as st
import pandas as pd

import pymongo
import certifi

from streamlit_echarts import st_echarts
import folium
from streamlit_folium import st_folium, folium_static

import requests
from requests.structures import CaseInsensitiveDict

# MongoDB connection setup
ca = certifi.where()
MONGO_URI = st.secrets["mongo"]["host"]
MONGO_URI1 = st.secrets["mongo1"]["host"]
MONGO_URI2 = st.secrets["mongo2"]["host"]

GEOAPIFY = st.secrets["geoapify"]["key"]

@st.cache_resource
def init_connection():
    return pymongo.MongoClient(MONGO_URI, tlsCAFile=ca)

client = init_connection()

def parse_quarter(q_str):
    year = int(q_str[:4])
    quarter = int(q_str[-1])
    return pd.Period(year=year, quarter=quarter, freq='Q')


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
        
        # Rental Analysis
        st.markdown("""
            <h4>🏢 Rental Trends Analysis</h4>
        """, unsafe_allow_html=True)
        
        # Fetch rental data
        rental_data = pd.DataFrame(list(tourism_db.rents_quarterly.find()))

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

        transactions_data = pd.DataFrame(list(tourism_db.transactions_df_quarterly_data.find()))

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

            # Fetch rental data
            rental_data = pd.DataFrame(list(tourism_db.rents_quarterly.find()))

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
    try:
        tourism_db = client.tourism_db
        
        # Fetch and process data with proper alignment
        rental_data = pd.DataFrame(list(tourism_db.rents_quarterly.find()))
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
        gdp_data = pd.DataFrame(list(tourism_db.gdp_quarterly_current_prices_df.find()))
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
        cpi_data = pd.DataFrame(list(tourism_db.consumer_price_index_monthly_df.find()))
        cpi_data['Time Period'] = pd.to_datetime(cpi_data['Time Period'])
        cpi_quarterly = cpi_data.resample('QE', on='Time Period')['Value'].mean() \
            .to_frame('CPI')

        # Population data
        population_data = pd.DataFrame(list(tourism_db.population_indicators_df.find()))
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
        
        col1, col2 = st.columns([2,1])
        
        with col1:
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
            
            
        with col2:
            st.markdown("<h4> 📈 Data Coverage</h4>", unsafe_allow_html=True)
            st.write(f"Time period: {correlation_df.index.min()} to {correlation_df.index.max()}")
            st.write(f"Number of quarters: {len(correlation_df)}")
            st.write("Data completeness:")
            for col in correlation_df.columns:
                pct_complete = (correlation_df[col].notna().sum() / len(correlation_df) * 100).round(1)
                st.write(f"{col}: {pct_complete}%")
        
        
            st.markdown("<h4> 🔍 Key Insights</h4>", unsafe_allow_html=True)
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
                st.markdown(f"""
                    <div style='padding:10px; background-color:#f0f2f6; border-radius:5px; margin:5px;'>
                        <b>{corr['factor1']}</b> vs <b>{corr['factor2']}</b><br>
                        {'Strong' if abs(corr['correlation']) > 0.7 else 'Moderate'} 
                        {'positive' if corr['correlation'] > 0 else 'negative'} 
                        correlation: {corr['correlation']:.2f}
                    </div>
                """, unsafe_allow_html=True)
                
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
