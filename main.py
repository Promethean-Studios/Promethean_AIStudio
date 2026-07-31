import os
import re
import time
import base64
import requests
import streamlit as st
from groq import Groq

# ------------------------------------------------------------------
# 1. PAGE CONFIG & CLEAN STUDIO THEME CSS
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Promethean Studio", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS focused on high contrast and preserving Streamlit icons
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;600&display=swap');
    
    /* Clean text styling without breaking Streamlit icon fonts */
    body, p, h1, h2, h3, h4, .stMarkdown {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main App Background */
    [data-testid="stAppViewContainer"], .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* Hide top branding header but keep sidebar button functional */
    #MainMenu, footer {
        visibility: hidden;
    }
    
    /* Code block fonts */
    code, pre, .stCodeBlock {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* User Chat Bubble (Odd) - Light Gray */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F8F9FA !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
    }
    [data-testid="stChatMessage"]:nth-child(odd) p,
    [data-testid="stChatMessage"]:nth-child(odd) span {
        color: #1A1A1A !important;
    }
    
    /* AI Chat Bubble (Even) - Dark Charcoal with Red Accent */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1E1E1E !important;
        border-left: 4px solid #E83223 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
    }
    [data-testid="stChatMessage"]:nth-child(even) p,
    [data-testid="stChatMessage"]:nth-child(even) span,
    [data-testid="stChatMessage"]:nth-child(even) div,
    [data-testid="stChatMessage"]:nth-child(even) strong {
        color: #F5F5F7 !important;
    }
    
    /* Interactive Button Styles */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# 2. AGENT REGISTRY, AVATARS & PROMPTS
# ------------------------------------------------------------------
AGENT_ROSTER = {
    "Titan": "openai/gpt-oss-120b",
    "Mnemosyne": "llama-3.3-70b-versatile",
    "Coeus": "llama-3.3-70b-versatile",
    "Theia": "llama-3.3-70b-versatile",
    "Oceanus": "llama-3.1-8b-instant",
    "Iapetus": "llama-3.3-70b-versatile",
    "Phoebe": "llama-3.3-70b-versatile"
}

AGENT_AVATARS = {
    "Titan": "https://cdn.discordapp.com/attachments/1525238408710979766/1532594925911281854/titanlogo_1.png?ex=6a6d6bc0&is=6a6c1a40&hm=2fb5f3f10f2ddb73c1c9371c7ef91fbbcd686dd43fb7880cf764efe222700cdd",
    "Mnemosyne": "https://cdn.discordapp.com/attachments/1525238474586853447/1532595548778004550/Screenshot_2026-07-30_11.39.34_PM-removebg-preview.png?ex=6a6d6c55&is=6a6c1ad5&hm=13670f4f8edf10ec587c45f3617def6981a871f93e877abfcf99c92bfe4317d2",
    "Coeus": "https://cdn.discordapp.com/attachments/1525238517079347433/1532595488522506250/Screenshot_2026-07-30_11.39.44_PM-removebg-preview.png?ex=6a6d6c46&is=6a6c1ac6&hm=b324cedfbce142a4f6772a921394fcbbd850e5fd1a9f5d44a3fb4a370a31486e",
    "Theia": "https://cdn.discordapp.com/attachments/1527841726772023296/1532595456289411145/Screenshot_2026-07-30_11.40.00_PM-removebg-preview.png?ex=6a6d6c3f&is=6a6c1abf&hm=df918b4ff93188c32fe15502176637fefdc3b47f197234f07e5920302756d35c",
    "Oceanus": "https://cdn.discordapp.com/attachments/1527841824402706443/1532595423963779162/Screenshot_2026-07-30_11.40.07_PM-removebg-preview.png?ex=6a6d6c37&is=6a6c1ab7&hm=791034b7f8db699bbb726675a94788abd9b3e617dc8210dd1125e250929f6c58",
    "Iapetus": "https://cdn.discordapp.com/attachments/1527841993210728499/1532595398911463444/Screenshot_2026-07-30_11.40.12_PM-removebg-preview.png?ex=6a6d6c31&is=6a6c1ab1&hm=be919f421b0b99cc5ad3ffcf61fa5ee8c5191c86cc6e8c02cfa126665d523b99",
    "Phoebe": "https://cdn.discordapp.com/attachments/1527842097443508375/1532594886401069196/Screenshot_2026-07-30_11.40.22_PM-removebg-preview.png?ex=6a6d6bb7&is=6a6c1a37&hm=bc287b8f53d40e4ab03974de334f5b9c6023db345b35f7a1156d2010e98a5f86"
}

AGENT_PROMPTS = {
    "Titan": "You are Titan, the heavy-duty 120B orchestrator. Be casual, direct, and honest. Provide clean, safe, and helpful responses.",
    "Mnemosyne": "You are Mnemosyne, the priority memory pipeline. Your goal is to maintain deep context across sessions. Keep track of user preferences. Be casual, honest, and helpful.",
    "Coeus": "You are Coeus, the multi-agent teamwork and deep-thinking core. You break down tasks into sub-tasks and critically analyze code. Be casual, honest, and helpful.",
    "Theia": "You are Theia, the visual data analyzer. You provide design feedback, identify UI bugs, and generate CSS. Be casual, honest, and helpful.",
    "Oceanus": "You are Oceanus, the ultimate routing engine and web intelligence coordinator. Be casual, honest, and helpful.",
    "Iapetus": "You are Iapetus, the bridge to physical reality. You specialize in low-level hardware instructions (C++ for Arduino, MicroPython). Be casual, honest, and helpful.",
    "Phoebe": "You are Phoebe, the proactive code supervisor. You scan architectures and predict bugs before they compile. Be casual, honest, and helpful."
}

# ------------------------------------------------------------------
# 3. SESSION STATE, ROUTING & TAVILY WEB SEARCH
# ------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "loading" not in st.session_state:
    st.session_state.loading = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "workspace_code" not in st.session_state:
    st.session_state.workspace_code = "# Active Code Workspace Initialized\n"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

def extract_code(text):
    """Safely extracts code blocks without breaking raw markdown rendering."""
    bt = chr(96) * 3
    pattern = re.escape(bt) + r'(?:[\w]*\n)?(.*?)' + re.escape(bt)
    code_blocks = re.findall(pattern, text, re.DOTALL)
    if code_blocks:
        return "\n\n".join(code_blocks)
    return None

def fetch_tavily_web_search(query):
    """Performs real-time web search via Tavily API."""
    tavily_key = ""
    try:
        tavily_key = st.secrets.get("TAVILY_API_KEY", "")
    except Exception:
        tavily_key = os.environ.get("TAVILY_API_KEY", "")
        
    if not tavily_key:
        return None
        
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": tavily_key, "query": query, "search_depth": "basic", "max_results": 3},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                snippets = [f"- [{r.get('title')}]({r.get('url')}): {r.get('content')}" for r in results]
                return "\n".join(snippets)
    except Exception:
        return None
    return None

def route_intent(prompt, client):
    router_sys = "You are an intent router. Read the user's prompt and output ONLY ONE name: Titan, Mnemosyne, Coeus, Theia, Oceanus, Iapetus, Phoebe."
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": router_sys}, {"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=10
        )
        choice = response.choices[0].message.content.strip().title()
        return choice if choice in AGENT_ROSTER else "Titan"
    except Exception:
        return "Titan" 

def get_groq_client():
    key = st.session_state.api_key
    if not key:
        try:
            key = st.secrets["GROQ_FREE_TIER_KEY"]
        except Exception:
            return None
    try:
        return Groq(api_key=key)
    except Exception:
        return None

# ------------------------------------------------------------------
# 4. AUTHENTICATION & LOADING GATES
# ------------------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("<br><br><br><h1 style='text-align: center; font-weight: 600;'>Welcome to Promethean Studio</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555;'>Secure Developer Gateway</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="background: #F8F9FA; padding: 2.5rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 12px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        auth_mode = st.radio("Select Access Tier", ["Free Daily Limit (30k)", "Bring Your Own Key (Groq)"])
        
        temp_key = ""
        if auth_mode == "Bring Your Own Key (Groq)":
            temp_key = st.text_input("Enter Groq API Key", type="password")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Initialize Core Connection", use_container_width=True):
            st.session_state.api_key = temp_key
            st.session_state.authenticated = True
            st.session_state.loading = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if st.session_state.loading:
    st.markdown("""
        <style>
            video {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                object-fit: cover !important;
                z-index: 999999 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    try:
        st.video("Copy of Promethean Studio.mp4", autoplay=True)
    except Exception:
        st.info("Video File 'Copy of Promethean Studio.mp4' not found. Bypassing animation...")
        time.sleep(2)
            
    time.sleep(6) 
    st.session_state.loading = False
    st.rerun()

# ------------------------------------------------------------------
# 5. MAIN STUDIO UI & SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("### System Controls")
    st.markdown("---")
    
    # Live Tavily Web Search Toggle (Ensures variable is always defined)
    st.markdown("### 🌐 Web Intelligence")
    enable_web_search = st.toggle("Enable Live Web Search (Tavily)", value=True)
    
    st.markdown("---")
    st.markdown("### Model Parameters")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    sys_prompt = st.text_area(
        "Base Instructions", 
        "You are a helpful, casual AI assistant. Provide clean, safe, and friendly responses.",
        height=100
    )
    
    st.markdown("---")
    st.markdown("### Session Actions")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    with col_b:
        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.markdown("---")
    st.markdown("### 🌐 Community Hub")
    st.markdown("[💬 Join our Discord](https://discord.gg/pXfXFWbu3T)")
    st.markdown("[📺 YouTube Channel](https://youtube.com/@titanaioffcial?si=Q3vgj6velbJGeNvJ)")
    st.markdown("[💻 GitHub Repository](https://github.com/Promethean-Studios)")

top_col1, top_col2 = st.columns([1, 1])
with top_col1:
    selected_agent = st.selectbox(
        "Active Agent Pipeline",
        ["Auto-Select (Intent Router)"] + list(AGENT_ROSTER.keys())
    )

chat_col, code_col = st.columns([1.2, 1])

# --- LEFT COLUMN: CHAT INTERFACE ---
with chat_col:
    st.markdown("### Communication Pipeline")
    chat_container = st.container(height=550)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                avatar = "👤"
            else:
                agent_name = msg.get("agent_name", "Titan")
                avatar = AGENT_AVATARS.get(agent_name, "⚡")
                
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    uploaded_image = None
    if selected_agent in ["Theia", "Auto-Select (Intent Router)"]:
        uploaded_image = st.file_uploader("Upload UI Screenshot for Theia", type=["png", "jpg", "jpeg"])

    user_input = st.chat_input("Enter command directives to Promethean...")

# --- RIGHT COLUMN: CODE WORKSPACE ---
with code_col:
    st.markdown("### Active Workspace")
    st.download_button(
        label="Download Workspace Code",
        data=st.session_state.workspace_code,
        file_name="promethean_workspace.py",
        mime="text/plain",
        use_container_width=True
    )
    st.code(st.session_state.workspace_code, language="python")

# ------------------------------------------------------------------
# 6. EXECUTION LOGIC
# ------------------------------------------------------------------
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            
    client = get_groq_client()
    if not client:
        err_msg = "Error: Unable to connect to Groq. Please check your API Key or secrets.toml."
        st.session_state.chat_history.append({"role": "assistant", "content": err_msg, "agent_name": "Titan"})
        st.rerun()

    active_agent = selected_agent
    if selected_agent == "Auto-Select (Intent Router)":
        active_agent = route_intent(user_input, client)
    
    model_to_use = AGENT_ROSTER.get(active_agent, "llama-3.3-70b-versatile")
    
    agent_identity = AGENT_PROMPTS.get(active_agent, AGENT_PROMPTS["Titan"])
    full_system_prompt = f"{sys_prompt}\n\n[YOUR DIRECTIVE]: {agent_identity}"
    
    messages = [{"role": "system", "content": full_system_prompt}]
    
    for msg in st.session_state.chat_history[-5:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    current_content = user_input
    
    # --- LIVE TAVILY WEB SEARCH INJECTION ---
    if enable_web_search:
        web_results = fetch_tavily_web_search(user_input)
        if web_results:
            current_content += f"\n\n[SYSTEM NOTE - Real-Time Web Context from Tavily]:\n{web_results}\n(Use this information to answer the user's prompt if relevant.)"

    if uploaded_image and active_agent == "Theia":
        base64_img = base64.b64encode(uploaded_image.read()).decode('utf-8')
        current_content = [
            {"type": "text", "text": current_content},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
        ]
        
    messages.append({"role": "user", "content": current_content})

    avatar = AGENT_AVATARS.get(active_agent, "⚡")
    with chat_container:
        with st.chat_message("assistant", avatar=avatar):
            message_placeholder = st.empty()
            full_response = f"**[{active_agent}]** "
            
            try:
                stream = client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    temperature=temperature,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")
                        
                message_placeholder.markdown(full_response)
                
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": full_response, 
                    "agent_name": active_agent
                })
                
                extracted = extract_code(full_response)
                if extracted:
                    st.session_state.workspace_code = extracted
                
                st.rerun()

            except Exception as e:
                error_alert = f"I encountered an error executing this pipeline: {str(e)}"
                message_placeholder.markdown(error_alert)
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": error_alert, 
                    "agent_name": "Titan"
                })