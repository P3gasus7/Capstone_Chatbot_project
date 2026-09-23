"""
CSC-128 Capstone: Moments Notice booking assistant
Shawn Canady

Streamlit interface for the grounded bot. Answers only come from the
knowledge base in knowledge.py -- if nothing relevant is retrieved, the
model is never called, and a fixed refusal string is returned directly
from code instead.
"""
import streamlit as st
from groq import Groq

from retriever import Retriever

REFUSAL = (
    "I do not have that information about booking Moments Notice. "
    "Please reach out to the band directly for details."
)

GROUNDED_PROMPT = """You are the booking assistant for the band Moments Notice.
Answer the visitor's question using ONLY the reference text between the <reference> tags below.

Rules:
- If the reference text does not contain the answer, respond with exactly this sentence and nothing else: "{refusal}"
- Do not use any knowledge from outside the reference text.
- Do not guess at prices, dates, distances, percentages, or any other numbers that are not stated in the reference text.
- Keep your answer under three sentences.

<reference>
{context}
</reference>
"""


@st.cache_resource
def get_retriever():
    return Retriever()


@st.cache_resource
def get_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


def answer(question):
    """
    Return (answer_text, sources). Sources is an empty list when the
    bot refuses, since a refusal has nothing to attribute.
    """
    retriever = get_retriever()
    hits = retriever.search(question)

    # Short circuit: if retrieval found nothing, the model is never
    # called at all. The refusal comes straight from code, not from
    # hoping the model's instructions hold with an empty context.
    if not hits:
        return REFUSAL, []

    context = retriever.build_context(hits)
    sources = ["{} ({})".format(doc["source"], doc["id"]) for doc, score in hits]

    client = get_client()
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": GROUNDED_PROMPT.format(refusal=REFUSAL, context=context),
            },
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content, sources


st.title("Moments Notice — Booking Assistant")
st.write(
    "Ask about booking Moments Notice for your event: pricing, "
    "availability policy, setlist and style, or performance details."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("sources"):
            st.caption("Source: " + "; ".join(message["sources"]))

question = st.chat_input("Ask a question about booking Moments Notice")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    reply, sources = answer(question)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "sources": sources}
    )
    with st.chat_message("assistant"):
        st.write(reply)
        if sources:
            st.caption("Source: " + "; ".join(sources))
