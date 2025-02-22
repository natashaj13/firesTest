import streamlit as st
import folium
import tensorflow as tf
from streamlit_folium import st_folium
import random
import numpy as np
import pandas as pd
from joblib import load
import math
import datetime

from getData import get_weather_data
from getData import get_fire_data

st.set_page_config(
    page_title="FireWatch",  # Title that will appear in the browser tab
    page_icon="🔥",          # Icon that will appear in the browser tab (can use text or image)
)

@st.cache_resource
def load_model():
    return load('model.joblib')

model = load_model()

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_weather_data_cached(latitude, longitude):
    return get_weather_data(latitude, longitude)

@st.cache_data(ttl=600)
def get_fire_data_cached(latitude, longitude):
    return get_fire_data(latitude, longitude)

# Function to prepare data for the model
def prepare_data(input_data):
   data = input_data.split()
   user_df = pd.DataFrame([data], columns=[
      'month', 'temp', 'RH', 'wind', 'rain',
   ])
   user_df['month'] = pd.to_numeric(user_df['month'])
   user_df['temp'] = pd.to_numeric(user_df['temp'])
   user_df['RH'] = pd.to_numeric(user_df['RH'])
   user_df['wind'] = pd.to_numeric(user_df['wind'])
   user_df['rain'] = pd.to_numeric(user_df['rain'])

   return user_df

# Function to make predictions (modify according to your model's input requirements)
def predict(processed_data):
   # Preprocess input data if necessary (e.g., scaling, reshaping, etc.)
   #  input_data = np.array(input_data).reshape(1, -1)  # Example
   prediction = model.predict(processed_data)
   return prediction

def is_within_radius(predicted_radius, distance):
   """
   Determines if a given point is within the circle defined by a predicted radius 
   with a ±20% margin of error.

   :param predicted_radius: The predicted radius of the circle.
   :param point: A tuple (x, y) representing the coordinates of the point.
   :param center: The center of the circle (default is (0, 0)).

   :return: A message indicating whether the point is inside the circle or not.
   """
   # Calculate the radius of the predicted area (convert units)
   predicted_radius *= 100
   danger_radius = math.sqrt(predicted_radius / (math.pi))

   # Calculate the actual radius range (80% to 120% of predicted radius)
   # min_radius = danger_radius * 0.8
   max_radius = danger_radius * 1.2

   # Check if the point is within the circle's range
   if distance <= max_radius:
      return f"You are within the high-risk radius of {danger_radius:.3} km."
   else:
      return f"You are safe from the nearest fire."

def print_result(prediction, fire_data):
   point = (latitude, longitude)  # Example point coordinates
   result = is_within_radius(prediction, fire_data["distance"])
   return result

#styles
st.markdown("""
    <style>
    /* Custom theme */
    .css-1d391kg {background-color: black; color: white;}  /* General page background color */

    /* Title styling */
    h1 {
        text-align: center;
        color: #FF5733;
        font-family: 'Tahoma';
    }

    html,
    body {
        font-family: 'Tahoma', sans-serif;
    }
    
    .map-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 5px;
        margin-left: 30px;
        margin-right: 30px;
        padding-top: 0rem;
        padding-bottom: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

#navigation bar
st.markdown("""
    <style>
    .css-18e3th9 { 
        padding-top: 0rem; 	
        padding-bottom: 0rem; 
    }

    body {
        margin: 0;
        padding: 0;
    }
    .navbar {
        background-color: #FF5733;
        padding: 5px;
        text-align: center;
        top: 0;
        margin-top: 0px;
        margin-bottom: 20px;
        width: 100%;
        z-index: 1000;
    }

    .navbar a {
        color: white;
        padding: 7px 10px;
        text-decoration: none;
        font-size: 18px;
        display: inline-block;
    }

    .navbar a:hover {
        background-color: #ddd;
        color: black;
        transition: 0.3s ease-in;
    }
    .content {
        margin-top: 60px; /* Add margin to push content below the navbar */
    }

    .footer {
        padding: 5px 0;
        bottom: 0;
        margin-bottom: 0;
        margin-top: 50px;
    }

    .footer a {
        color: #FF5733; 
        font-size: 20px; 
        text-decoration: none;
    }

    .footer a:hover {
        color: gray;
        text-decoration: underline;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def create_map(lat, lon, zoom=5):
   m = folium.Map(location=[40.0, -120.0], zoom_start=5)
   folium.Marker(location=[40.0, -120.0]).add_to(m) 
   m.add_child(folium.ClickForMarker()) # Add click functionality to the map

   fire_data = pd.read_csv('df_fire.csv')

   for index, row in fire_data.iterrows():
      latitude = row['latitude']  # Replace 'latitude' with the actual column name
      longitude = row['longitude']  # Replace 'longitude' with the actual column name
      folium.Marker(
         location=[latitude, longitude],
         icon=folium.Icon(color='red', icon='fire')
      ).add_to(m)
   return m

#tabs (links)
st.markdown("""
    <div class="navbar">
        <a href="?page=Home" class="{% if page == 'Home' %}active{% endif %}">Home</a>
        <a href="?page=resources" class="{% if page == 'resources' %}active{% endif %}">Resources</a>
    </div>
""", unsafe_allow_html=True)

# Get query params from URL
query_params = st.experimental_get_query_params()

#current page from URL query param
tab = query_params.get("page", ["Home"])[0]  # Default to "home" if no parameter

if tab == "Home":
    # Click
    st.markdown("""
        <h1 style='color: #FF5733; font-family: Tahoma; font-size: 50px;'>FireWatch</h1>
        <p style='color: #E28743; font-family: Tahoma; font-size: 20px; text-align: center; padding-right: 10px;'>&nbsp;A Real-Time Wildfire Predictor</p>
    """, unsafe_allow_html=True)
    st.write('')
    st.write('')
    st.markdown("<h3 style='text-align: center; font-family: 'Tahoma'; color: white;'>Click on the map to select a location:</h3>", unsafe_allow_html=True)

    st.markdown('<div class="map-container">', unsafe_allow_html=True)

    # Initialize map
    m = create_map(40.0, -120.0)
   
    # Render map 
    map_result = st_folium(m, width=700)

    st.markdown('</div>', unsafe_allow_html=True)

    if map_result and "last_clicked" in map_result: 
        clicked_location = map_result["last_clicked"]

        if clicked_location and "lat" in clicked_location and "lng" in clicked_location:
            latitude = clicked_location["lat"]
            longitude = clicked_location["lng"]
                        
            weather_data = get_weather_data_cached(latitude, longitude)
            fire_data = get_fire_data_cached(latitude, longitude)

            if weather_data:
                current_date = datetime.datetime.now()
                user_input = str(current_date.month-1) + " "
                user_input += str(weather_data['temperature']) + " "
                user_input += str(weather_data['humidity']) + " "
                user_input += str(weather_data['wind_speed']) + " "
                user_input += str(weather_data['precipitation'])
                input_data = prepare_data(user_input)
                prediction = predict(input_data)
                result = print_result(prediction, fire_data)
                if "safe" in result.lower():
                    color = "#90EE90"
                else:
                    color = "#FF5733"
                st.markdown(f"<p style='text-align: center; font-size: 24px; color: {color}'>{result}</p>", unsafe_allow_html=True)

    # Display latitude and longitude separately
            st.markdown(
                f"""
                <p style='text-align: center;'>
                    <strong>Latitude:</strong> {latitude:.6f} <br>
                    <strong>Longitude:</strong> {longitude:.6f}
                </p>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<p style='text-align: center;'>Please click on the map.</p>", unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; color: #FF5733;'>This model predicts the likelihood of wildfire occurrence based on environmental factors. Click on the map to choose a location, and the model will fetch environmental data for prediction.</p>", unsafe_allow_html=True)


    # Footer
    st.markdown("""
        <div style="text-align: center; font-size: 14px; color: gray;">
            <p>Data sources: National Weather Service, Fire Prediction Model</p>
        </div>
    """, unsafe_allow_html=True)

elif tab == "resources":
    st.markdown("<h1 style='text-align: center; color: #FF5733; font-family: Tahoma; font-size: 50px;'>Safety Tips</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white; font-family: Tahoma;'>Information and resources related to wildfire safety and prevention</h3>", unsafe_allow_html=True)
    st.write('')
    st.write('')
    try:
        st.image(
        "https://cdn.kqed.org/wp-content/uploads/sites/10/2025/01/GettyImages-2193000280-1020x653.jpg",
        caption="Crowd watching Palisades Fire from Santa Monica, California on January 8, 2025. (Tiffany Rose/Getty Images)"
        )
    except Exception as e:
        st.error(f"An error occurred: {e}")
   
    st.markdown("<p style='text-align: center; color: #FF5733; font-size: 26px;'>Tips to be Prepared</p>", unsafe_allow_html=True)
    st.markdown("<p style ='text-align: left; color: white; font-size: 18px;'>Have emergency supplies prepared. Pack essentials like water, food, and medicine.</p>", unsafe_allow_html=True)
    st.markdown("<p style ='text-align: left; color: white; font-size: 18px;'>Monitor fires and the weather around you regularly.</p>", unsafe_allow_html=True)
    st.markdown("<p style ='text-align: left; color: white; font-size: 18px;'>Learn emergency skills such as CPR and First Aid.</p>", unsafe_allow_html=True)
    st.markdown("<p style ='text-align: left; color: white; font-size: 18px;'>Plan to not have access to electricity or the internet.</p>", unsafe_allow_html=True)
    st.markdown("<p style ='text-align: left; color: white; font-size: 18px;'>Keep personal records safe.</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class='footer' style='text-align: left; font-size: 20px;'>
        <p style='text-align: center; color: #FF5733; font-size: 26px;'>Resources</p>
        <p><a href='https://www.disasterassistance.gov/' target='_blank'>Federal Emergency Management Agency (FEMA)</a></p>
        <p><a href='https://readyforwildfire.org/prepare-for-wildfire/wildfire-action-plan/' target='_blank'>Create your own wildfire action plan</a></p>
        <p><a href='https://namica.org/wildfires/' target='_blank'>General information about wildfires</a></p>
        <p><a href='https://www.samhsa.gov/find-help/helplines/disaster-distress-helpline' target='_blank'>Helpline for disaster counseling</a></p>
        <p><a href='https://www.cdfa.ca.gov/firerecovery/' target='_blank'>Wildfire recovery resources</a></p>
        <p><a href='https://readyforwildfire.org/post-wildfire/who-can-help' target='_blank'>Organizations that can help with wildfire recovery</a></p>
    </div>
    """, unsafe_allow_html=True)
