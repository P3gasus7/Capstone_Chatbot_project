"""
CSC-128 Capstone: Moments Notice booking assistant
Shawn Canady

Streamlit interface only. Routing, slot filling, and conversation state
live in dialog.py; retrieval, refusal, and error messages live in
grounded_bot.py. This file just draws the page and passes messages
through.
"""
import logging

import streamlit as st

from dialog import DialogState, handle_turn
from grounded_bot import make_client
from retriever import Retriever


@st.cache_resource
def get_retriever():
    # Cached so the TF-IDF index is built once per server, not on every
    # Streamlit rerun (which happens after every chat message).
    return Retriever()


@st.cache_resource
def build_client(api_key):
    return make_client(api_key)


def get_client():
    """
    Return a Groq client, or None if the key is not configured.

    Only the successfully built client is cached. A missing key is
    re-checked on every question, so pasting the key into the Secrets
    panel fixes the app without waiting for a restart.
    """
    try:
        return build_client(st.secrets["GROQ_API_KEY"])
    except Exception as err:
        # Missing key or missing secrets file: the page still loads and
        # the visitor sees a message instead of a traceback. The log
        # line (type only, never the key) tells the owner which it was.
        logging.getLogger("moments_notice").warning(
            "Could not build Groq client: %s", type(err).__name__
        )
        return None


def render_message(message):
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.warning(message["content"])
        else:
            st.write(message["content"])
        parts = []
        if message.get("intent") and not message.get("error"):
            parts.append("Intent: " + message["intent"].replace("_", " "))
        if message.get("sources"):
            parts.append("Source: " + "; ".join(message["sources"]))
        if parts:
            st.caption(" \u00b7 ".join(parts))


st.title("Moments Notice — Booking Assistant")
st.write(
    "Ask about booking Moments Notice for your event: pricing, "
    "availability policy, setlist and style, or performance details."
)
st.caption(
    "You are chatting with an automated assistant, not a person. It only "
    "answers from the band's booking information."
)
st.caption(
    "Privacy: your question is sent to a third-party AI service (Groq) to "
    "write the answer. Conversations are not saved by this app. Please "
    "do not type personal or payment information."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "dialog" not in st.session_state:
    # What the bot remembers between turns: the slot-filling flow in
    # progress, the slots filled so far, and the last topic.
    st.session_state.dialog = DialogState()

for message in st.session_state.messages:
    render_message(message)

question = st.chat_input("Ask a question about booking Moments Notice")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    render_message(st.session_state.messages[-1])

    # The client may be None (no API key). handle_turn still serves the
    # deterministic intents, and only the faq path reports the problem.
    with st.spinner("Looking that up..."):
        reply = handle_turn(
            question, st.session_state.dialog, get_retriever(), get_client()
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": reply.text,
            "sources": reply.sources,
            "intent": reply.intent,
            "error": not reply.ok,
        }
    )
    render_message(st.session_state.messages[-1])
