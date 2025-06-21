import os
import re
import requests
from datetime import datetime
import google.generativeai as genai
import streamlit as st
from pyngrok import ngrok

# --- Load API keys from environment variables ---
openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
ngrok_auth_token = os.getenv('NGROK_AUTH_TOKEN')

# --- Configure Gemini AI ---
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# --- Intent detectors ---
def is_date_query(text):
    pattern = re.compile(
        r"\b(what(?:'s| is)?\s+(today|date|day)|current\s+(date|day)|today['s]*\s+date|what\s+time\s+is\s+it)\b",
        re.IGNORECASE
    )
    return bool(pattern.search(text))

def is_weather_query(text):
    pattern = re.compile(r"\b(weather|temperature|forecast|rain|snow|sunny|cloudy)\b", re.IGNORECASE)
    return bool(pattern.search(text))

# --- City extraction ---
def extract_city(text):
    noise_words = {"today", "now", "please", "right", "currently", "tomorrow", "this", "week", "tonight"}
    match = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)", text, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
    else:
        tokens = text.strip().split()
        city = tokens[-1]
    city = re.sub(r"[?.!,]*$", "", city)
    words = city.lower().split()
    filtered = [word for word in words if word not in noise_words]
    if not filtered:
        return None
    return ' '.join(filtered).title()

# --- Weather agent ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"The weather in {city} is {desc} with a temperature of {temp:.2f}°C."
    else:
        st.write(f"[Debug] Weather API error: {response.status_code} | {response.json()}")
        return f"Sorry, couldn't fetch weather for {city}."

# --- Date agent ---
def get_current_date():
    now = datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."

# --- General AI agent ---
def query_google_ai(prompt):
    context_prompt = f"""
You are a helpful assistant answering general knowledge questions. Assume today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
Respond clearly and concisely.

User asked: "{prompt}"
"""
    response = model.generate_content(context_prompt)
    return response.text.strip()

# --- Dispatcher ---
def chatbot(user_input, debug=False):
    if is_date_query(user_input):
        if debug:
            st.write("[Debug] Routed to Date Agent")
        return get_current_date()
    elif is_weather_query(user_input):
        if debug:
            st.write("[Debug] Routed to Weather Agent")
        city = extract_city(user_input)
        if city:
            return get_weather(city)
        else:
            return "Please specify a city for the weather query."
    else:
        if debug:
            st.write("[Debug] Routed to Gemini AI Agent")
        return query_google_ai(user_input)

# --- Streamlit UI ---
st.title("🤖 Weather + AI Bot")
st.markdown("Ask about weather, dates, travel plans, or general AI questions.")

debug_mode = st.checkbox("Show debug info")
user_input = st.text_input("Enter your message:")

if user_input:
    response = chatbot(user_input, debug=debug_mode)
    st.markdown(f"**Bot:** {response}")

# --- ngrok setup to expose app ---
if ngrok_auth_token:
    ngrok.set_auth_token(ngrok_auth_token)
    ngrok.kill()
    public_url = ngrok.connect(8501)
    print(f"Streamlit app is running at: {public_url}")
    st.write(f"[Live URL]({public_url})")
else:
    st.write("NGROK_AUTH_TOKEN not found in environment variables, please set it to expose the app publicly.")
