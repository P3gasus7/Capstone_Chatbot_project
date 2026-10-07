# Moments Notice — Booking Assistant

**Author:** Shawn Canady — CSC-128 Capstone
**Live app:** TODO paste your public Streamlit URL here

## What it does

This is a grounded chatbot for **Moments Notice**, a jazz/R&B band, built
to answer prospective clients' questions about booking the band for an
event. It answers only from a fixed knowledge base (`knowledge.py`):
deposit and cancellation policy, travel fees, advance booking, equipment,
genres/style, event types, set length, and arrival/setup. If a question
isn't covered by that knowledge base, the bot refuses rather than
guessing. The page tells visitors they are talking to software, not a
person.

## How to run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Add your key to `.streamlit/secrets.toml` locally (never committed):

```toml
GROQ_API_KEY = "your-key-here"
```

On Streamlit Community Cloud, paste the same line into the app's
**Secrets** panel. Set the main file path to `app.py`.

Tests (neither needs an API key):

```bash
python test_retriever.py        # retrieval: 9 real questions + 1 unrelated
python test_phrasing.py         # same question, formal/casual/dialect phrasing
python test_bot.py              # failure paths: rate limit, outage, bad key, blank answer, etc.
python test_model_properties.py # checks the property checkers (add --live with a key to test the model)
```

`TRANSCRIPT_TESTS.md` holds two scripted conversations to run by hand on the live app.

## Files

| File | What's in it |
|---|---|
| `app.py` | Streamlit interface only: draws the page, caches the retriever and client |
| `grounded_bot.py` | Bot logic: retrieval, refusal short circuit, grounding prompt, error handling |
| `retriever.py` | TF-IDF retrieval: stemming, analyzer, threshold-based search |
| `knowledge.py` | 9 knowledge chunks, each with an id and source label |
| `test_retriever.py` | Retrieval tests for all 9 chunks plus a negative case |
| `test_phrasing.py` | Bias check: varied phrasings must reach the same chunk |
| `test_bot.py` | Failure-path tests using a fake Groq client |
| `test_model_properties.py` | Property tests for model output (length, refusal, no invented numbers) |
| `TRANSCRIPT_TESTS.md` | Scripted conversations with a per-turn checklist |
| `DESIGN.md` | Design document |
| `.gitignore` | Lists `.streamlit/secrets.toml` |
| `requirements.txt` | streamlit, groq, scikit-learn, all pinned |

## How the threshold was set

`test_retriever.py` prints the top match and score for 10 test
questions (9 real questions, 1 that's genuinely unrelated). Running it
gave real matches scoring between **0.122 and 0.324**, while an
unrelated question ("How do I pay my college tuition?") scored
**0.0** against every chunk. `DEFAULT_THRESHOLD = 0.10` in
`retriever.py` sits below every true match and above the unrelated
score, so it was set from that printed evidence rather than guessed.

## Error handling

Every failure path returns a plain message and never a traceback.
`test_bot.py` raises each failure on purpose and checks the result:

| Failure | What the visitor sees |
|---|---|
| Rate limit | "The assistant is busy right now. Please wait a minute and try again." |
| Network error or timeout | Asks them to check their connection and retry |
| Bad or missing API key | Says the assistant isn't set up correctly and to contact the band |
| Any other API failure | Generic "ran into a problem" message with next step |
| Blank model answer | Asks them to rephrase |
| Empty or overlong question | Asks for a question, or a shorter one |
| Nothing relevant retrieved | The fixed refusal, returned from code without calling the model |

## Scope, refusal, and hand-off

- **Refuses:** anything not in the booking knowledge base (legal or financial advice, weather, payment methods it has no information on, prices not stated). The refusal sentence tells the visitor to contact the band.
- **Hands off to a human:** custom quotes, confirming a specific date's availability, and contract questions go to the band directly.

## Privacy and disclosure

The page states that visitors are talking to software, and that their question is sent to a third-party AI service (Groq). The app does not store conversations, and the notice asks visitors not to type personal or payment information.

## Bias and phrasing

`test_phrasing.py` asks the same question formally, casually, and in different dialects (for example "how long you playin" and "yo how much down payment to lock in the band"). Early runs showed casual wording retrieving the wrong chunk, so the chunks now include everyday synonyms such as "down payment" and "out of town". Known remaining limit: very loose phrasing can still miss, for example "what if my party is out of town, extra cost?" retrieves the cancellation policy.

## Source attribution

Every answer is shown with the source label(s) of the chunk(s) it was
grounded in (e.g. "Booking Policy"), displayed as a caption under the
response.

Refusals never show a source, because a refusal has nothing to
attribute. For answers, the caption lets you tell apart two kinds of
failure. If the bot answers with a wrong or invented detail **and a
source is shown**, the retriever found the right area but the model went
beyond it, which is a **prompt failure**. If the bot gives a wrong answer
from the **wrong chunk** (for example a deposit question citing the
set-length chunk), that is a **retrieval failure**. Without the caption,
both look the same to the visitor, and there'd be no way to tell whether
to fix the retriever or the grounding prompt.

## Hallucination testing (five near-miss questions)

These five questions are close to the bot's topic but not answered by
any chunk. For each, the retriever *did* find a related chunk (the
"Retrieved chunk(s)" column is real output from `retriever.py`), so the
model was called and any refusal has to come from the grounding prompt.

| # | Question | Retrieved chunk(s) | Actual bot response | Refused correctly? |
|---|---|---|---|---|
| 1 | Do you take requests for country songs? | event_types (0.118), genres_style (0.114) | TODO | TODO |
| 2 | Can I pay the deposit with a credit card? | deposit_policy (0.179) | TODO | TODO |
| 3 | Do you provide catering or a DJ in between sets? | set_length (0.113) | TODO | TODO |
| 4 | Is there a discount for booking multiple events? | advance_booking (0.140) | TODO | TODO |
| 5 | Can you learn a special song for our first dance? | event_types (0.118), genres_style (0.114) | TODO | TODO |

**Result:** TODO after running the five questions on the live app, say
which of the three (threshold, chunk wording, or grounding prompt)
deserves the credit for each correct refusal. For any invented answer,
say which one you changed and what happened on the retest.
