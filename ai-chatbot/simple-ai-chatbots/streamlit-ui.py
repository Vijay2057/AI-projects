import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/api/chat"


st.set_page_config(
    page_title="My Chatbot",
    page_icon="🤖"
)

st.title("🤖 My Chatbot")


# --------------------------------
# Conversation history
# --------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------
# Display history
# --------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# --------------------------------
# User input
# --------------------------------

user_message = st.chat_input("Ask something...")


if user_message:

    # Display user message

    with st.chat_message("user"):
        st.markdown(user_message)

    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })


    # --------------------------------
    # Call FastAPI
    # --------------------------------

    response = requests.post(
        API_URL,
        json={
            "message": user_message
        }
    )


    # --------------------------------
    # Handle response
    # --------------------------------

    if response.status_code == 200:

        data = response.json()

        assistant_message = data["response"]

    else:

        assistant_message = (
            f"API Error: {response.status_code}"
        )


    # --------------------------------
    # Display assistant
    # --------------------------------

    with st.chat_message("assistant"):
        st.markdown(assistant_message)


    # Save assistant response

    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_message
    })