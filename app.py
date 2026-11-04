import streamlit as st
from agent import chat_with_assistant

# Page Configuration
st.set_page_config(
    page_title="CarePlus Clinic — AI Assistant",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Dark Minimalist Professional CSS
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Global Typography & Dark Background */
html, body, .stApp {
    background-color: #090D16 !important;
    color: #F1F5F9 !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Main Container Spacing */
.block-container {
    padding-top: 2.2rem !important;
    padding-bottom: 6rem !important;
    max-width: 780px !important;
}

/* Custom Hero Header */
.hero-box {
    text-align: center;
    padding: 1.5rem 1rem 1.25rem 1rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #1E293B;
}

.hero-badge {
    display: inline-block;
    background: rgba(56, 189, 248, 0.1);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.25);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}

.hero-title {
    font-size: 2rem;
    font-weight: 700;
    color: #F8FAFC;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    color: #94A3B8;
    font-size: 0.95rem;
    font-weight: 400;
    margin: 0;
}

/* Chat Message Containers */
[data-testid="stChatMessage"] {
    background-color: #111827 !important;
    border: 1px solid #1E293B !important;
    border-radius: 14px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.85rem !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
}

/* Force Left Alignment & High Contrast Inside Chat Messages */
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li,
[data-testid="stChatMessageContent"] span,
[data-testid="stChatMessageContent"] div {
    color: #E2E8F0 !important;
    text-align: left !important;
    line-height: 1.65 !important;
    font-size: 0.96rem !important;
}

[data-testid="stChatMessageContent"] strong {
    color: #38BDF8 !important;
    font-weight: 600 !important;
}

[data-testid="stChatMessageContent"] ul,
[data-testid="stChatMessageContent"] ol {
    margin-top: 0.4rem !important;
    margin-bottom: 0.6rem !important;
    padding-left: 1.25rem !important;
}

[data-testid="stChatMessageContent"] li {
    margin-bottom: 0.35rem !important;
}

/* Quick Prompt Cards (Buttons) */
div.stButton > button {
    background-color: #111827 !important;
    color: #E2E8F0 !important;
    border: 1px solid #1E293B !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.86rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    min-height: 64px !important;
}

div.stButton > button:hover {
    border-color: #38BDF8 !important;
    background-color: #1E293B !important;
    color: #FFFFFF !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(56, 189, 248, 0.12) !important;
}

/* Bottom Chat Input Bar */
[data-testid="stBottom"] > div {
    background-color: #090D16 !important;
    border-top: 1px solid #1E293B !important;
}

div[data-testid="stChatInput"] {
    background-color: #111827 !important;
    border: 1px solid #334155 !important;
    border-radius: 14px !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: #38BDF8 !important;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.15) !important;
}

div[data-testid="stChatInput"] textarea {
    color: #F8FAFC !important;
    font-size: 0.95rem !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid #1E293B !important;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background: transparent !important;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Sidebar for UX Controls & Clinic Quick Info
with st.sidebar:
    st.markdown("### 🩺 CarePlus Clinic")
    st.caption("AI-Powered Reception & Booking")
    st.markdown("---")
    st.markdown(
        "**🕒 Timings:**\nMon – Sat: 9:00 AM – 5:00 PM PKT\n*(Closed on Sundays)*\n\n"
        "**💳 Payments:**\nCash, Bank Transfer, SadaPay, JazzCash, Cards"
    )
    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Hero Header
st.markdown(
    """
    <div class="hero-box">
        <div class="hero-badge">● Live AI Receptionist</div>
        <h1 class="hero-title">🩺 CarePlus Clinic</h1>
        <p class="hero-subtitle">Ask about services, fees, & timings, or book an appointment synced with Google Calendar</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

def process_query(prompt: str):
    """Formats chat history and fetches response from backend agent."""
    history_tuples = []
    msgs = st.session_state.messages
    for i in range(0, len(msgs) - 1, 2):
        if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
            history_tuples.append((msgs[i]["content"], msgs[i + 1]["content"]))

    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        response = chat_with_assistant(prompt, history_tuples)
    except TypeError:
        response = chat_with_assistant(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})

# Render Existing Chat History
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🩺"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Starter Prompt Cards (Only visible when chat is empty)
if not st.session_state.messages:
    st.markdown(
        "<p style='color: #64748B; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.6rem;'>Suggested Queries</p>",
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns(3)
    prompts = [
        ("💼 Services & Fees", "What services do you offer and what are your charges?"),
        ("🕒 Clinic Timings", "What are your clinic timings and cancellation policy?"),
        ("📅 Book Appointment", "I want to book a Dental Checkup for tomorrow.")
    ]
    for col, (label, full_prompt) in zip([col1, col2, col3], prompts):
        if col.button(label, use_container_width=True):
            with st.spinner("Connecting to CarePlus AI..."):
                process_query(full_prompt)
            st.rerun()

# Main Chat Input
if user_prompt := st.chat_input("Ask about treatments, prices, or book a slot..."):
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar="🩺"):
        with st.spinner("Checking clinic records..."):
            history_tuples = []
            msgs = st.session_state.messages
            for i in range(0, len(msgs) - 1, 2):
                if msgs[i]["role"] == "user" and msgs[i + 1]["role"] == "assistant":
                    history_tuples.append((msgs[i]["content"], msgs[i + 1]["content"]))

            try:
                reply = chat_with_assistant(user_prompt, history_tuples)
            except TypeError:
                reply = chat_with_assistant(user_prompt)

            st.markdown(reply)

    st.session_state.messages.append({"role": "user", "content": user_prompt})
    st.session_state.messages.append({"role": "assistant", "content": reply})