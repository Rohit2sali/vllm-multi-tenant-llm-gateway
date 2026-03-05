import streamlit as st
import requests
import json

st.set_page_config(page_title="vLLM Multi-Tenant UI", layout="centered")

st.title("🤖 vLLM Gateway Interface")
st.markdown("---")


# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("📝 Register New User")
    with st.form("register_form"):
        new_user_id = st.text_input("Choose a User ID", placeholder="e.g., rohit_dev")
        submit_register = st.form_submit_button("Generate API Key")

        if submit_register and new_user_id:
            try:
                res = requests.post("http://server:8000/register", json={"user_id": new_user_id})
                if res.status_code == 200:
                    data = res.json()
                    st.success("Registration Successful!")
                    st.info(f"**Your API Key:** `{data['api_key']}`\n\n*Copy this now! It won't be shown again.*")
                else:
                    st.error("Registration failed.")
            except Exception as e:
                st.error("Could not connect to backend.")

    st.divider()

    # Consolidated Authentication and Settings
    st.header("🔑 Authentication")
    api_key = st.text_input("Enter API Key", type="password", placeholder="this-127")
    user_id_field = st.text_input("User ID (Label)", value="test_user")
    
    st.header("⚙️ Model Settings")
    max_tokens = st.slider("Max Tokens", 16, 512, 128, key="max_tokens_slider_1")
    
    st.divider()
    
    if st.button("💾 Save Configuration", use_container_width=True):
        if not api_key:
            st.warning("⚠️ Please enter an API Key before saving.")
        else:
            st.session_state['saved_api_key'] = api_key
            st.session_state['saved_user_id'] = user_id_field
            st.session_state['saved_max_tokens'] = max_tokens
            st.success("✅ All information has been saved!")

# ----------------- CHAT UI -----------------

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Message the LLM..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    url = "http://server:8000/generate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "user_id": user_id_field,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "stream": True
    }

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            with requests.post(url, headers=headers, json=payload, stream=True) as r:
                if r.status_code == 401:
                    st.error("Invalid API Key. Please check the sidebar.")
                elif r.status_code == 200:
                    for line in r.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data:"):
                                data_str = decoded[5:].strip()
                                
                                if data_str == "[DONE]":
                                    break
                                
                                try:
                                    chunk = json.loads(data_str)
                                    if "token" in chunk:
                                        full_response += chunk["token"]
                                        response_placeholder.markdown(full_response + "▌")
                                except json.JSONDecodeError:
                                    continue
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error(f"Server Error: {r.status_code}")
                    
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to FastAPI server. Is your backend running on port 8000?")


# streamlit run frontend.py --server.port 8501
