import os
import re
import json
import time
import requests
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

# ------------------------------------------------------------------
# 1. PAGE CONFIG & ROBOTO CONDENSED STUDIO THEME CSS
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Promethean Studio", 
    page_icon="https://i.ibb.co/Cpmd4TCH/Screenshot-2026-08-01-2-34-26-AM-removebg-preview.png",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Custom CSS focused on Roboto Condensed typography, high contrast, and clean layout
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:ital,wght@0,300;0,400;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap');
    
    /* Apply Roboto Condensed safely without breaking Streamlit Material Icons */
    body, p, h1, h2, h3, h4, label, .stMarkdown, .stSelectbox, .stTextInput, .stRadio { 
        font-family: 'Roboto Condensed', sans-serif !important; 
    }
    
    /* Explicitly protect Streamlit icons from being overridden */
    .stIcon, .material-symbols-rounded, span[data-baseweb="icon"] {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }
    
    [data-testid="stAppViewContainer"], .stApp { background-color: #FFFFFF !important; }
    #MainMenu, footer { visibility: hidden; }
    
    /* Preserve monospace font for code blocks */
    code, pre, .stCodeBlock { font-family: 'JetBrains Mono', monospace !important; }
    
    /* User Chat Bubble */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F8F9FA !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
    }
    [data-testid="stChatMessage"]:nth-child(odd) p, [data-testid="stChatMessage"]:nth-child(odd) span { 
        color: #1A1A1A !important; 
        font-family: 'Roboto Condensed', sans-serif !important;
    }
    
    /* AI Chat Bubble */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1E1E1E !important;
        border-left: 4px solid #E83223 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 0.75rem !important;
    }
    [data-testid="stChatMessage"]:nth-child(even) p, [data-testid="stChatMessage"]:nth-child(even) span, 
    [data-testid="stChatMessage"]:nth-child(even) div, [data-testid="stChatMessage"]:nth-child(even) strong { 
        color: #F5F5F7 !important; 
        font-family: 'Roboto Condensed', sans-serif !important;
    }
    
    .stButton > button { 
        font-family: 'Roboto Condensed', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 8px !important; 
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

AGENT_DESCRIPTIONS = {
    "Auto-Select (Intent Router)": "Automatically scans your prompt and assigns the best agent for the job.",
    "Titan": "Heavy-duty orchestrator. Best for complex logic, general reasoning, and heavy lifting.",
    "Mnemosyne": "Priority memory pipeline. Maintains deep context and tracks your preferences.",
    "Coeus": "Multi-agent teamwork core. Breaks down complex tasks and critically analyzes code.",
    "Theia": "Visual data & interface analyzer. Perfect for UI bugs and layout design.",
    "Oceanus": "Web intelligence coordinator. Scours the internet for real-time data.",
    "Iapetus": "Hardware specialist. Writes low-level C++, Arduino, and MicroPython code.",
    "Phoebe": "Proactive code supervisor. Scans architectures and predicts bugs before compilation."
}

AGENT_AVATARS = {
    "Titan": "https://i.ibb.co/KctT09yy/titanlogo-1.png",
    "Mnemosyne": "https://i.ibb.co/Zp69ydmW/Screenshot-2026-07-30-11-39-34-PM-removebg-preview.png",
    "Coeus": "https://i.ibb.co/b05kHkf/Screenshot-2026-07-30-11-39-44-PM.png",
    "Theia": "https://i.ibb.co/0yf2hQNK/Screenshot-2026-07-30-11-40-00-PM-removebg-preview.png",
    "Oceanus": "https://i.ibb.co/whhXGrXm/Screenshot-2026-07-30-11-40-07-PM-removebg-preview.png",
    "Iapetus": "https://i.ibb.co/cKLpth4K/Screenshot-2026-07-30-11-40-12-PM-removebg-preview.png",
    "Phoebe": "https://i.ibb.co/B5C8chd3/Screenshot-2026-07-30-11-40-22-PM-removebg-preview.png"
}

USER_AVATAR = "https://i.ibb.co/PvVH62RP/user-logo-removebg-preview.png"
DEFAULT_AVATAR = "https://i.ibb.co/Cpmd4TCH/Screenshot-2026-08-01-2-34-26-AM-removebg-preview.png"

AGENT_PROMPTS = {
    "Titan": "You are Titan, the heavy-duty 120B orchestrator. Be casual, direct, and honest. Provide clean, safe, and helpful responses.",
    "Mnemosyne": "You are Mnemosyne, the priority memory pipeline. Your goal is to maintain deep context across sessions. Keep track of user preferences. Be casual, honest, and helpful.",
    "Coeus": "You are Coeus, the multi-agent teamwork and deep-thinking core. You break down tasks into sub-tasks and critically analyze code. Be casual, honest, and helpful.",
    "Theia": "You are Theia, the visual data and interface analyzer. You provide design feedback, identify UI bugs, and analyze layouts. Be casual, honest, and helpful.",
    "Oceanus": "You are Oceanus, the ultimate routing engine and web intelligence coordinator. Be casual, honest, and helpful.",
    "Iapetus": "You are Iapetus, the bridge to physical reality. You specialize in low-level hardware instructions (C++ for Arduino, MicroPython). Be casual, honest, and helpful.",
    "Phoebe": "You are Phoebe, the proactive code supervisor. You scan architectures and predict bugs before they compile. Be casual, honest, and helpful."
}

enable_web_search = True
temperature = 0.7
sys_prompt = "You are a helpful, casual AI assistant. Provide clean, safe, and friendly responses."
selected_agent = "Auto-Select (Intent Router)"

# ------------------------------------------------------------------
# 3. SESSION STATE & CLOUD LOGIC
# ------------------------------------------------------------------
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "loading" not in st.session_state: st.session_state.loading = False
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "workspace_code" not in st.session_state: st.session_state.workspace_code = "# Active Code Workspace Initialized\n"
if "api_key" not in st.session_state: st.session_state.api_key = ""
if "firebase_uid" not in st.session_state: st.session_state.firebase_uid = None
if "firebase_token" not in st.session_state: st.session_state.firebase_token = None

def get_fb_key():
    try:
        if "firebase" in st.secrets and "apiKey" in st.secrets["firebase"]:
            return st.secrets["firebase"]["apiKey"]
        if "FIREBASE_API_KEY" in st.secrets:
            return st.secrets["FIREBASE_API_KEY"]
    except Exception:
        pass
    return os.environ.get("FIREBASE_API_KEY", None)

def get_fb_project():
    try:
        if "firebase" in st.secrets and "projectId" in st.secrets["firebase"]:
            return st.secrets["firebase"]["projectId"]
        if "FIREBASE_PROJECT_ID" in st.secrets:
            return st.secrets["FIREBASE_PROJECT_ID"]
    except Exception:
        pass
    return os.environ.get("FIREBASE_PROJECT_ID", None)

def firebase_auth(email, password, mode="login"):
    api_key = get_fb_key()
    if not api_key: 
        return {"error": {"message": "Firebase API Key missing. Please configure [firebase] apiKey in Streamlit Secrets."}}
    
    endpoint = "signInWithPassword" if mode == "login" else "signUp"
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:{endpoint}?key={api_key}"
    try:
        res = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": {"message": f"Network error during authentication: {str(e)}"}}

def firestore_save_state():
    project_id = get_fb_project()
    uid = st.session_state.firebase_uid
    token = st.session_state.firebase_token
    if not project_id or not uid or not token: return False
    
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/users/{uid}"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "fields": {
            "chat_history": {"stringValue": json.dumps(st.session_state.chat_history)},
            "workspace_code": {"stringValue": st.session_state.workspace_code}
        }
    }
    try:
        res = requests.patch(url, headers=headers, json=payload, timeout=10)
        return res.status_code == 200
    except Exception:
        return False

def firestore_load_state():
    project_id = get_fb_project()
    uid = st.session_state.firebase_uid
    token = st.session_state.firebase_token
    if not project_id or not uid or not token: return False
    
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/users/{uid}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if "fields" in data:
                st.session_state.chat_history = json.loads(data["fields"].get("chat_history", {}).get("stringValue", "[]"))
                st.session_state.workspace_code = data["fields"].get("workspace_code", {}).get("stringValue", "# Workspace Loaded")
                return True
    except Exception:
        pass
    return False

# --- UTILITIES & EXPORTS ---
def extract_code(text: str):
    bt = chr(96) * 3
    pattern = re.escape(bt) + r'(?:[\w]*\n)?(.*?)' + re.escape(bt)
    code_blocks = re.findall(pattern, text, re.DOTALL)
    if code_blocks: return "\n\n".join(code_blocks)
    return None

def fetch_tavily_web_search(query: str):
    tavily_key = st.secrets.get("TAVILY_API_KEY", os.environ.get("TAVILY_API_KEY", ""))
    if not tavily_key: return None
    try:
        response = requests.post("https://api.tavily.com/search", json={"api_key": tavily_key, "query": query, "search_depth": "basic", "max_results": 3}, timeout=5)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results: return "\n".join([f"- [{r.get('title', 'Source')}]({r.get('url', '#')}): {r.get('content', '')}" for r in results])
    except Exception: pass
    return None

def route_intent(prompt: str, client: Groq):
    router_sys = "You are an intent router. Output ONLY ONE name: Titan, Mnemosyne, Coeus, Theia, Oceanus, Iapetus, Phoebe."
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": router_sys}, {"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=10
        )
        raw_choice = response.choices[0].message.content
        choice = raw_choice.strip().title() if raw_choice else "Titan"
        return choice if choice in AGENT_ROSTER else "Titan"
    except Exception: return "Titan" 

def get_groq_client():
    key = st.session_state.api_key
    if not key:
        try: key = st.secrets["GROQ_FREE_TIER_KEY"]
        except Exception: return None
    try: return Groq(api_key=key)
    except Exception: return None

def generate_export(format_type):
    """Generates clean exports of the current chat session."""
    if format_type == "json":
        return json.dumps(st.session_state.chat_history, indent=2)
    elif format_type == "txt":
        out = "Promethean Studio - Chat Transcript\n\n"
        for msg in st.session_state.chat_history:
            role = "User" if msg["role"] == "user" else msg.get("agent_name", "Promethean AI")
            out += f"[{role}]:\n{msg['content']}\n\n"
        return out
    elif format_type == "md":
        out = "# Promethean Studio - Chat Transcript\n\n"
        for msg in st.session_state.chat_history:
            role = "**User**" if msg["role"] == "user" else f"**{msg.get('agent_name', 'Promethean AI')}**"
            out += f"{role}:\n\n{msg['content']}\n\n---\n\n"
        return out
    return ""

# ------------------------------------------------------------------
# 4. AUTHENTICATION & CLOUD GATEWAY
# ------------------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://i.ibb.co/jvhbLFxr/OGIN.png", use_container_width=True)
        st.markdown('<div style="background: #F8F9FA; padding: 2.5rem; border-radius: 12px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 12px rgba(0,0,0,0.05);">', unsafe_allow_html=True)
        
        auth_mode = st.radio("Select Access Tier", ["Guest (Local Session)", "Cloud Account (Firebase)"])
        
        temp_key = ""
        email = ""
        password = ""
        
        if auth_mode == "Cloud Account (Firebase)":
            st.markdown("#### Promethean Cloud Login")
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            
            c1, c2 = st.columns(2)
            with c1: btn_login = st.button("Log In", use_container_width=True)
            with c2: btn_signup = st.button("Sign Up", use_container_width=True)
            
            temp_key = st.text_input("Groq API Key (Optional for Cloud)", type="password")
            
            if btn_login or btn_signup:
                if not email or not password:
                    st.error("Please enter both email and password.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    mode = "login" if btn_login else "signup"
                    result = firebase_auth(email, password, mode)
                    
                    if "error" in result:
                        st.error(f"Authentication Failed: {result['error']['message']}")
                    else:
                        st.session_state.firebase_uid = result["localId"]
                        st.session_state.firebase_token = result["idToken"]
                        st.session_state.api_key = temp_key
                        st.session_state.authenticated = True
                        st.session_state.loading = True
                        st.rerun()
                        
        else:
            temp_key = st.text_input("Enter Groq API Key", type="password")
            if st.button("Initialize Local Session", use_container_width=True):
                st.session_state.api_key = temp_key
                st.session_state.authenticated = True
                st.session_state.loading = True
                st.rerun()
                
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

if st.session_state.loading:
    st.markdown("""
        <style>
            video { position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; object-fit: cover !important; z-index: 999999 !important; }
        </style>
    """, unsafe_allow_html=True)
    try:
        st.video("Copy of Promethean Studio.mp4", autoplay=True)
    except Exception:
        st.info("Video file not found. Bypassing intro animation...")
        time.sleep(2)
            
    time.sleep(6) 
    st.session_state.loading = False
    
    if st.session_state.firebase_uid:
        firestore_load_state()
        
    st.rerun()

# ------------------------------------------------------------------
# 5. MAIN STUDIO UI & SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.image("https://i.ibb.co/JwsZ54vR/Promethean-Studios-2.png", use_container_width=True)
    
    if st.session_state.firebase_uid:
        st.success("Cloud Account Connected")
        st.markdown("### Cloud Sync")
        sync_c1, sync_c2 = st.columns(2)
        with sync_c1:
            if st.button("⎙ Save", use_container_width=True):
                if firestore_save_state(): st.toast("Saved to Firestore!")
                else: st.toast("Failed to save.")
        with sync_c2:
            if st.button("⎋ Load", use_container_width=True):
                if firestore_load_state(): 
                    st.toast("Loaded from Firestore!")
                    st.rerun()
                else: st.toast("Failed to load.")
        st.markdown("---")
        
    st.markdown("### Agent Capabilities")
    with st.container(height=280):
        for a_name, a_desc in AGENT_DESCRIPTIONS.items():
            if a_name != "Auto-Select (Intent Router)":
                st.markdown(f"<div style='margin-bottom: 12px; line-height: 1.2;'><b>{a_name}</b><br><span style='color: #888888; font-size: 0.85em;'>{a_desc}</span></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### System Controls")
    enable_web_search = st.toggle("Enable Live Web Search (Tavily)", value=True)
    
    st.markdown("---")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    sys_prompt = st.text_area("Base Instructions", "You are a helpful, casual AI assistant. Provide clean, safe, and friendly responses.", height=100)
    
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
            
    st.markdown("### Export Transcripts")
    exp_c1, exp_c2, exp_c3 = st.columns(3)
    with exp_c1:
        st.download_button("MD", data=generate_export("md"), file_name="chat.md", mime="text/markdown", use_container_width=True)
    with exp_c2:
        st.download_button("TXT", data=generate_export("txt"), file_name="chat.txt", mime="text/plain", use_container_width=True)
    with exp_c3:
        st.download_button("JSON", data=generate_export("json"), file_name="chat.json", mime="application/json", use_container_width=True)

# Top Banner Header
st.image("https://i.ibb.co/7NyFcpCK/Promethean-Studios-1.png", use_container_width=True)

top_col1, top_col2 = st.columns([1, 1])
with top_col1:
    selected_agent = st.selectbox("Active Agent Pipeline", ["Auto-Select (Intent Router)"] + list(AGENT_ROSTER.keys()))
    st.markdown(f"<p style='color: #888888; font-size: 0.9em; margin-top: -10px; margin-bottom: 20px;'>{AGENT_DESCRIPTIONS[selected_agent]}</p>", unsafe_allow_html=True)

chat_col, code_col = st.columns([1.2, 1])

# --- LEFT COLUMN: CHAT INTERFACE ---
with chat_col:
    st.markdown("### Communication Pipeline")
    chat_container = st.container(height=550)
    
    with chat_container:
        for msg in st.session_state.chat_history:
            msg_avatar = USER_AVATAR if msg["role"] == "user" else AGENT_AVATARS.get(msg.get("agent_name", "Titan"), DEFAULT_AVATAR)
            with st.chat_message(msg["role"], avatar=msg_avatar):
                st.markdown(msg["content"])

    user_input = st.chat_input("Enter command directives to Promethean...")

# --- RIGHT COLUMN: INTERACTIVE ARTIFACTS WORKSPACE ---
with code_col:
    st.markdown("### Active Workspace")
    
    code_content = st.session_state.workspace_code
    lower_code = code_content.lower()
    
    code_lang = "python"
    if "<html" in lower_code or "<!doctype" in lower_code:
        code_lang = "html"
    elif "function " in lower_code and "console.log" in lower_code:
        code_lang = "javascript"
    elif "#include" in lower_code or "std::" in lower_code:
        code_lang = "cpp"
        
    tab_code, tab_preview, tab_doc = st.tabs(["Code Editor", "Live Preview", "Document Reader"])
    
    with tab_code:
        st.download_button(
            label="Download Workspace File",
            data=code_content,
            file_name=f"workspace_export.{'html' if code_lang == 'html' else 'py'}",
            mime="text/plain",
            use_container_width=True
        )
        st.code(code_content, language=code_lang)
        
    with tab_preview:
        if code_lang == "html" or "<style" in lower_code or "<div" in lower_code or "<svg" in lower_code:
            components.html(code_content, height=550, scrolling=True)
        else:
            st.info("Live Preview is optimized for Web Content (HTML, CSS, JS, or SVG). Ask an agent to build a UI to see it live here!")
            
    with tab_doc:
        st.markdown(code_content)

# ------------------------------------------------------------------
# 6. EXECUTION LOGIC
# ------------------------------------------------------------------
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user", avatar=USER_AVATAR):
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
    
    if enable_web_search:
        web_results = fetch_tavily_web_search(user_input)
        if web_results:
            current_content += f"\n\n[SYSTEM NOTE - Real-Time Web Context from Tavily]:\n{web_results}\n(Use this information to answer the user's prompt if relevant.)"

    messages.append({"role": "user", "content": current_content})

    bot_avatar = AGENT_AVATARS.get(active_agent, DEFAULT_AVATAR)
    with chat_container:
        with st.chat_message("assistant", avatar=bot_avatar):
            message_placeholder = st.empty()
            full_response = f"**[{active_agent}]** "
            
            try:
                stream = client.chat.completions.create(
                    model=model_to_use, messages=messages, temperature=temperature, stream=True
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta is not None:
                        full_response += delta
                        message_placeholder.markdown(full_response + "▌")
                        
                message_placeholder.markdown(full_response)
                st.session_state.chat_history.append({"role": "assistant", "content": full_response, "agent_name": active_agent})
                
                extracted = extract_code(full_response)
                if extracted: st.session_state.workspace_code = extracted
                
                if st.session_state.firebase_uid:
                    firestore_save_state()
                
                st.rerun()

            except Exception as e:
                error_alert = f"I encountered an error executing this pipeline: {str(e)}"
                message_placeholder.markdown(error_alert)
                st.session_state.chat_history.append({"role": "assistant", "content": error_alert, "agent_name": "Titan"})