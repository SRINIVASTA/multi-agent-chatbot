import re
import requests
from datetime import datetime
import google.generativeai as genai
import streamlit as st

# --- Configure page ---
st.set_page_config(page_title="SRINIVASTA Multi-Agent Chatbot", page_icon="🤖")

# --- Initial Greeting (always shown) ---
st.toast("🎉 Welcome to SRINIVASTA Multi-Agent Chatbot!", icon="👋")
st.markdown("### 👋 Hello and welcome!")
st.markdown("This is a **multi-agent chatbot** powered by **Google Gemini AI** and **OpenWeather API**.")
st.markdown("You'll be able to ask about **weather**, **dates**, and general knowledge.")

# --- Initialize session state ---
if 'google_api_key' not in st.session_state:
    st.session_state.google_api_key = ""
if 'openweather_api_key' not in st.session_state:
    st.session_state.openweather_api_key = ""
if 'keys_saved' not in st.session_state:
    st.session_state.keys_saved = False

# --- API Key Entry ---
if not st.session_state.keys_saved:
    st.subheader("🔑 Enter Your API Keys")
    st.info("Please enter your Google API Key and OpenWeather API Key to continue.")

    with st.form("api_key_form"):
        google_key_input = st.text_input("Google API Key", type="password")
        openweather_key_input = st.text_input("OpenWeather API Key", type="password")
        submitted = st.form_submit_button("Save Keys")

        if submitted:
            if google_key_input.strip() and openweather_key_input.strip():
                st.session_state.google_api_key = google_key_input.strip()
                st.session_state.openweather_api_key = openweather_key_input.strip()
                st.session_state.keys_saved = True
                st.success("✅ Keys saved! Scroll down to use the chatbot.")
            else:
                st.error("❌ Please enter both API keys.")

    # --- Example Questions Below API Keys ---
    st.markdown("---")
    st.markdown("### 💡 Example Questions You Can Ask:")
    st.markdown("""
    - 🌤️ **What's the weather in Paris today?**  
    - 🤖 **Explain how transformers work in AI**  
    - 🧳 **Plan a 3-day trip to Visakhapatnam with budget tips**  
    - 🐍 **Generate a Python script to scrape a website**  
    """)

# --- Only load chatbot if keys are saved ---
if st.session_state.keys_saved:

    # --- Configure Gemini AI ---
    genai.configure(api_key=st.session_state.google_api_key)
    model = genai.GenerativeModel("gemini-2.0-flash-exp")

    # --- UI ---
    st.title("🤖 Weather + AI Chatbot")
    st.markdown("Ask about **weather**, **dates**, or general knowledge. Powered by OpenWeatherMap & Gemini AI.")

    def is_date_query(text):
        pattern = re.compile(
            r"\b(what(?:'s| is)?\s+(today|date|day)|current\s+(date|day)|today['s]*\s+date|what\s+time\s+is\s+it)\b",
            re.IGNORECASE
        )
        return bool(pattern.search(text))

    def is_weather_query(text):
        pattern = re.compile(r"\b(weather|temperature|forecast|rain|snow|sunny|cloudy)\b", re.IGNORECASE)
        return bool(pattern.search(text))

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

    def get_weather(city):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={st.session_state.openweather_api_key}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"The weather in {city} is **{desc}** with a temperature of **{temp:.1f}°C**."
        else:
            return f"❌ Sorry, couldn't fetch weather for **{city}**."

    def get_current_date():
        now = datetime.now()
        return f"📅 Today is **{now.strftime('%A, %B %d, %Y')}**."

    def query_google_ai(prompt):
        context_prompt = f"""
You are a helpful assistant answering general knowledge questions. Assume today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
Respond clearly and concisely.

User asked: "{prompt}"
"""
        response = model.generate_content(context_prompt)
        return response.text.strip()

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

    # --- Chatbot UI ---
    debug_mode = st.checkbox("🧪 Show debug info")
    user_input = st.text_input("💬 Ask something:")

    if user_input:
        response = chatbot(user_input, debug=debug_mode)
        st.markdown(f"**🤖 Bot:** {response}")
