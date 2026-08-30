import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from database_backend import chatbot, retrieve_all_thread, get_thread_messages

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Chatbot • LangGraph + SQLite",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling (Modern Dark Glassmorphism) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 950px;
    }

    /* Header styling */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.2rem 1.8rem;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        backdrop-filter: blur(12px);
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    .header-title {
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #60A5FA, #A78BFA, #F472B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }

    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(96, 165, 250, 0.12);
        color: #93C5FD;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }

    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
    }

    /* Suggestion Chips */
    .suggestion-box {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 1rem 0;
    }

    /* Streamlit Chat Messages customization */
    div[data-testid="stChatMessage"] {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    div[data-testid="stChatMessage"]:hover {
        border-color: rgba(96, 165, 250, 0.3);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)


# --- Load Threads from SQLite Database ---
db_threads = retrieve_all_thread()

if "thread_list" not in st.session_state:
    if db_threads:
        st.session_state.thread_list = sorted(list(db_threads))
        st.session_state.current_thread = st.session_state.thread_list[0]
    else:
        st.session_state.thread_list = ["Thread 1"]
        st.session_state.current_thread = "Thread 1"

if "current_thread" not in st.session_state or st.session_state.current_thread not in st.session_state.thread_list:
    st.session_state.current_thread = st.session_state.thread_list[0]

current_thread_id = st.session_state.current_thread


# --- Sidebar ---
with st.sidebar:
    st.markdown("### 💬 Chat Sessions (SQLite)")
    
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        new_thread_num = len(st.session_state.thread_list) + 1
        new_thread_name = f"Thread {new_thread_num}"
        while new_thread_name in st.session_state.thread_list:
            new_thread_num += 1
            new_thread_name = f"Thread {new_thread_num}"
        st.session_state.thread_list.append(new_thread_name)
        st.session_state.current_thread = new_thread_name
        st.rerun()

    st.markdown("---")
    st.markdown("#### Saved Threads")

    for thread_name in list(st.session_state.thread_list):
        col1, col2 = st.columns([4, 1])
        is_active = thread_name == st.session_state.current_thread
        
        with col1:
            btn_label = f"✨ {thread_name}" if is_active else f"💾 {thread_name}"
            if st.button(btn_label, key=f"select_{thread_name}", use_container_width=True, disabled=is_active):
                st.session_state.current_thread = thread_name
                st.rerun()
                
        with col2:
            if len(st.session_state.thread_list) > 1:
                if st.button("🗑️", key=f"del_{thread_name}", help=f"Remove {thread_name} from list"):
                    st.session_state.thread_list.remove(thread_name)
                    st.session_state.current_thread = st.session_state.thread_list[0]
                    st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ Database Engine")
    st.markdown("""
    - **Backend:** `database_backend.py`
    - **Checkpointer:** `SqliteSaver (chatbot.db)`
    - **LLM:** `Ollama (qwen3:1.7b)`
    - **Active Thread ID:**  
      `{}`
    """.format(current_thread_id))

    if st.button("🔄 Sync with Database", use_container_width=True):
        updated_threads = retrieve_all_thread()
        if updated_threads:
            for t in updated_threads:
                if t not in st.session_state.thread_list:
                    st.session_state.thread_list.append(t)
        st.rerun()


# --- Main Header ---
st.markdown(f"""
<div class="header-container">
    <div>
        <h1 class="header-title">🤖 LangGraph SQLite Chatbot</h1>
        <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.85rem;">
            Persistent multi-turn conversation backed by SQLite storage (chatbot.db)
        </p>
    </div>
    <div class="badge-pill">
        <div class="status-dot"></div>
        <span>{current_thread_id}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# --- Load Messages from SQLite for Active Thread ---
raw_messages = get_thread_messages(current_thread_id)

display_messages = []
for msg in raw_messages:
    role = "user" if isinstance(msg, HumanMessage) or getattr(msg, "type", "") == "human" else "assistant"
    content = msg.content if hasattr(msg, "content") else str(msg)
    display_messages.append({"role": role, "content": content})


# --- Quick Starter Prompts (if empty chat) ---
if not display_messages:
    st.markdown("<p style='color: #64748B; font-size: 0.9rem; margin-bottom: 6px;'>Try starting with one of these:</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    starter_prompts = [
        ("👋 Introduce Yourself", "Hello! Who are you and what can you do?"),
        ("🧠 Test SQLite Memory", "Hi, my favorite color is Blue. Save this in database!"),
        ("⚡ Coding Help", "Write a simple Python function to reverse a string.")
    ]
    
    selected_prompt = None
    with c1:
        if st.button(starter_prompts[0][0], use_container_width=True):
            selected_prompt = starter_prompts[0][1]
    with c2:
        if st.button(starter_prompts[1][0], use_container_width=True):
            selected_prompt = starter_prompts[1][1]
    with c3:
        if st.button(starter_prompts[2][0], use_container_width=True):
            selected_prompt = starter_prompts[2][1]

    if selected_prompt:
        config = {"configurable": {"thread_id": current_thread_id}}
        chatbot.invoke({"messages": [HumanMessage(content=selected_prompt)]}, config=config)
        st.rerun()


# --- Display Existing Chat Messages ---
for msg in display_messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])


# --- Chat Input & Execution with Streaming ---
user_input = st.chat_input("Type your message here...")

if user_input:
    # 1. Display user message immediately
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    # 2. Invoke LangGraph with SQLite thread checkpointer and stream tokens
    with st.chat_message("assistant", avatar="🤖"):
        try:
            CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {
            "thread_id": st.session_state["thread_id"]
        },
        "run_name": "chat_turn",
    }
            
            def stream_generator():
                for chunk, metadata in chatbot.stream(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=CONFIG,
                    stream_mode="messages"
                ):
                    if hasattr(chunk, "content") and chunk.content:
                        yield chunk.content
                    elif isinstance(chunk, str):
                        yield chunk
            
            # Stream tokens in real time
            response_text = st.write_stream(stream_generator())
            
            # Refresh to sync the state with SQLite
            st.rerun()

        except Exception as e:
            error_msg = f"⚠️ **Error streaming from graph:** `{str(e)}`"
            st.error(error_msg)
