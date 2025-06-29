import re
import requests
from datetime import datetime
import google.generativeai as genai
import streamlit as st

# --- Helper: Save API keys in session state ---
def save_api_keys():
    st.session_state.google_api_key = st.session_state.get("input_google_key", "").strip()
    st.session_state.openweather_api_key = st.session_state.get("input_openweather_key", "").strip()

# --- Check if keys are in session state ---
google_api_key = st.session_state.get("google_api_key")
openweather_api_key = st.session_state.get("openweather_api_key")

# --- If keys not set, show input forms ---
if not google_api_key or not openweather_api_key:
    st.title("🔑 Enter Your API Keys")
    st.info("Please enter your Google API Key and OpenWeather API Key to continue.")

    st.text_input("Google API Key", key="input_google_key", type="password")
    st.text_input("OpenWeather API Key", key="input_openweather_key", type="password")

    def save_and_reload():
        save_api_keys()
        st.experimental_rerun()

    st.button("Save API Keys", on_click=save_and_reload)

    st.stop()  # Stop further execution until keys are set

# --- Now that keys are set, configure Gemini AI ---
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# --- UI Title and Instructions ---
st.title("🤖 Weather + AI Bot")
st.markdown("Ask about **weather**, **dates**, or **general questions**. Powered by OpenWeatherMap & Gemini AI.")

# --- Intent Detectors ---
def is_date_query(text):
    pattern = re.compile(
        r"\b(what(?:'s| is)?\s+(today|date|day)|current\s+(date|day)|today['s]*\s+date|what\s+time\s+is\s+it)\b",
        re.IGNORECASE
    )
    return bool(pattern.search(text))

def is_weather_query(text):
    pattern = re.compile(r"\b(weather|temperature|forecast|rain|snow|sunny|cloudy)\b", re.IGNORECASE)
    return bool(pattern.search(text))

# --- City Extractor ---
def extract_city(text):
    noise_words = {"today", "now", "please", "right", "currently", "tomorrow", "this", "week", "tonight"}

    matches = re.findall(r"(?:in|for)\s+([a-zA-Z\s]+)", text, re.IGNORECASE)
    if matches:
        city = matches[-1].strip()
    else:
        tokens = text.strip().split()
        city = tokens[-1]

    city = re.sub(r"[?.!,]*$", "", city)
    words = city.lower().split()
    filtered = [word for word in words if word not in noise_words]
    if not filtered:
        return None
    return ' '.join(filtered).title()

# --- Weather Agent ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"The weather in {city} is **{desc}** with a temperature of **{temp:.1f}°C**."
    else:
        st.write(f"[Debug] Weather API error: {response.status_code} | {response.json()}")
        return f"❌ Sorry, couldn't fetch weather for **{city}**. Please check the city name."

# --- Date Agent ---
def get_current_date():
    now = datetime.now()
    return f"📅 Today is **{now.strftime('%A, %B %d, %Y')}**."

# --- Gemini AI Agent ---
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
            st.write("🛠️ [Debug] Routed to Date Agent")
        return get_current_date()
    elif is_weather_query(user_input):
        if debug:
            st.write("🛠️ [Debug] Routed to Weather Agent")
        city = extract_city(user_input)
        if city:
            return get_weather(city)
        else:
            return "🌍 Please specify a **city** for the weather."
    else:
        if debug:
            st.write("🛠️ [Debug] Routed to Gemini AI Agent")
        return query_google_ai(user_input)

# --- Main Chat UI ---
debug_mode = st.checkbox("🪛 Show debug info")
user_input = st.text_input("💬 Enter your message:")

if user_input:
    response = chatbot(user_input, debug=debug_mode)
    st.markdown(f"**🤖 Bot:** {response}")
