"""
CSC-128 Capstone: Moments Notice booking assistant
Shawn Canady

Bot logic only -- no Streamlit in this file. app.py owns the interface,
this file owns the decisions: retrieve, refuse, call the model, and turn
every failure into a message a visitor can act on. Keeping the two apart
means this file can be tested without a browser or an API key.

Answers only come from the knowledge base in knowledge.py. If nothing
relevant is retrieved, the model is never called and a fixed refusal
string is returned directly from code.
"""
import logging

import groq

from retriever import Retriever

logger = logging.getLogger("moments_notice")

MODEL = "openai/gpt-oss-20b"

# Cap on question length. Retrieval is cheap, but every character that
# reaches the model costs tokens, and no real booking question needs more.
MAX_QUESTION_CHARS = 500

REFUSAL = (
    "I do not have that information about booking Moments Notice. "
    "Please reach out to the band directly for details."
)

# One message per failure type. Each tells the visitor what happened and
# what to do next, and none of them expose a traceback or an exception
# string (which can leak request details).
MSG_EMPTY = "Please type a question about booking Moments Notice."
MSG_TOO_LONG = (
    "That question is a bit long for me. Please shorten it to a sentence "
    "or two and try again."
)
MSG_RATE_LIMIT = (
    "The assistant is busy right now. Please wait a minute and try again."
)
MSG_CONNECTION = (
    "I could not reach the assistant service. Please check your "
    "connection and try again in a moment."
)
MSG_AUTH = (
    "The assistant is not set up correctly on our end. Please contact the "
    "band directly while we fix it."
)
MSG_UNAVAILABLE = (
    "The assistant ran into a problem and could not answer. Please try "
    "again, or reach out to the band directly."
)
MSG_BLANK_ANSWER = (
    "I could not put together an answer to that. Please try rephrasing "
    "your question."
)

GROUNDED_PROMPT = """You are the booking assistant for the band Moments Notice.
Answer the visitor's question using ONLY the reference text between the <reference> tags below.

Rules:
- If the reference text does not contain the answer, respond with exactly this sentence and nothing else: "{refusal}"
- Do not use any knowledge from outside the reference text.
- Do not guess at prices, dates, distances, percentages, or any other numbers that are not stated in the reference text.
- Do not say what a number or percentage applies to (for example "of the total fee") unless the reference text says so.
- Keep your answer under three sentences.

<reference>
{context}
</reference>
"""


def make_client(api_key):
    """
    Build the Groq client. The SDK retries rate limits and transient
    errors itself with exponential backoff (two retries here), and the
    timeout keeps a stalled request from freezing the page; if every
    attempt fails, answer() turns the final error into a plain message.
    """
    return groq.Groq(api_key=api_key, timeout=20.0, max_retries=2)


def _call_model(client, question, context):
    """One model call. Raises groq exceptions; answer() handles them."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": GROUNDED_PROMPT.format(refusal=REFUSAL, context=context),
            },
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def answer(question, retriever, client):
    """
    Return (answer_text, sources, ok).

    sources is empty when the bot refuses or fails, since neither has
    anything to attribute. ok is False only for system failures (rate
    limit, outage, bad key); a refusal is a correct answer, so ok stays
    True and the interface does not style it as an error.
    """
    question = (question or "").strip()
    if not question:
        return MSG_EMPTY, [], False
    if len(question) > MAX_QUESTION_CHARS:
        return MSG_TOO_LONG, [], False

    hits = retriever.search(question)

    # Short circuit: if retrieval found nothing, the model is never
    # called at all. The refusal comes straight from code, not from
    # hoping the model's instructions hold with an empty context.
    if not hits:
        return REFUSAL, [], True

    context = retriever.build_context(hits)
    sources = ["{} ({})".format(doc["source"], doc["id"]) for doc, score in hits]

    try:
        text = _call_model(client, question, context)
    except groq.RateLimitError:
        logger.warning("Groq rate limit hit")
        return MSG_RATE_LIMIT, [], False
    except (groq.APIConnectionError, groq.APITimeoutError):
        logger.warning("Groq connection or timeout error")
        # APITimeoutError is a subclass of APIConnectionError in the SDK;
        # listing both keeps the intent obvious to the next reader.
        return MSG_CONNECTION, [], False
    except (groq.AuthenticationError, groq.PermissionDeniedError) as err:
        # Log the type and HTTP status only. Never log the key or the
        # full error text.
        logger.warning(
            "Groq rejected the request: %s (status %s)",
            type(err).__name__, getattr(err, "status_code", "?"),
        )
        return MSG_AUTH, [], False
    except Exception as err:
        logger.warning("Unexpected model error: %s", type(err).__name__)
        # Last resort so that no failure, including ones this code did
        # not anticipate, ever reaches the page as a traceback.
        return MSG_UNAVAILABLE, [], False

    # Reasoning models occasionally return no text. Treat that as a
    # failure rather than showing the visitor an empty chat bubble.
    if not text or not text.strip():
        return MSG_BLANK_ANSWER, [], False

    # A refusal has nothing to attribute. The model may refuse even when
    # retrieval found a loosely related chunk, so clear the sources here;
    # otherwise the visitor sees a "Source:" line under "I do not have
    # that information", which looks like the bot is citing its refusal.
    if REFUSAL in text:
        return REFUSAL, [], True

    return text.strip(), sources, True
