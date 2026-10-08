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

Beyond answering questions, it holds a conversation: it works out what
the visitor wants (four intents), asks for missing details (slot
filling), remembers them across turns, and computes a travel quote or a
booking-date check in plain code instead of asking the model.

## Required capabilities

| Capability | How the bot meets it | Where | Tested in |
|---|---|---|---|
| Four distinct intents | `faq`, `travel_quote`, `booking_check`, `handoff`, each handled differently (see table below) | `intents.py`, `dialog.py` | `test_intents.py` |
| Two entities through slot filling | Distance in miles (travel quote); event type and event date (booking check). The bot asks for whatever is missing | `entities.py`, `dialog.py` | `test_entities.py`, `test_dialog.py` |
| Conversation state across turns | Slots filled so far, the flow in progress, and the last topic persist between messages, so a side question does not lose the flow and "And when do I pay it?" resolves | `DialogState` in `dialog.py` | `test_dialog.py` |
| A language model for part of the response | Phrases the answer to faq questions from retrieved text | `grounded_bot.py` | `test_bot.py`, `test_model_properties.py` |
| Grounding in documents | Nine knowledge chunks, TF-IDF retrieval, threshold, refusal short circuit | `knowledge.py`, `retriever.py` | `test_retriever.py`, `test_phrasing.py` |
| Disclosure that it is software | Stated near the top of the page | `app.py` | transcript checks |
| Graceful failure when the API is down or rate limited | Every failure becomes a plain message; deterministic intents keep working with no API key | `grounded_bot.py`, `dialog.py` | `test_bot.py`, `test_dialog.py` |

| Intent | Example | What happens | Model called? |
|---|---|---|---|
| `faq` | "How much is the deposit?" | Retrieve the chunk, model phrases the answer, source shown. Nothing retrieved means the fixed refusal | Only when retrieval finds a chunk |
| `travel_quote` | "How much would travel cost?" | Asks for miles, then computes the fee from the travel policy (free within 25 miles, then 2 dollars per mile round trip) and shows the arithmetic | Never |
| `booking_check` | "I want to book you for my wedding" | Asks for event type and date, then checks the three-months-ahead guideline for popular spring and fall wedding dates | Never |
| `handoff` | "Can I get a custom quote?" | Fixed message sending custom quotes, date confirmation, and contracts to the band | Never |

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
python test_entities.py         # miles, event type, and date extraction
python test_intents.py          # the four intents, and that ordinary questions stay faq
python test_dialog.py           # multi-turn slot filling, state, hand-off, degraded modes
```

`TRANSCRIPT_TESTS.md` holds three scripted conversations to run by hand on the live app.

## Files

| File | What's in it |
|---|---|
| `app.py` | Streamlit interface only: draws the page, keeps the conversation state in the session |
| `dialog.py` | Conversation logic: intent routing, slot filling, state across turns, travel quote and booking check |
| `intents.py` | Classifies each message into one of four intents with ordered pattern rules |
| `entities.py` | Extracts miles, event type, and date from free text |
| `grounded_bot.py` | The faq path: retrieval, refusal short circuit, grounding prompt, error handling |
| `retriever.py` | TF-IDF retrieval: stemming, analyzer, threshold-based search |
| `knowledge.py` | 9 knowledge chunks, each with an id and source label |
| `test_retriever.py` | Retrieval tests for all 9 chunks plus a negative case |
| `test_phrasing.py` | Bias check: varied phrasings must reach the same chunk |
| `test_bot.py` | Failure-path tests using a fake Groq client |
| `test_entities.py` | Entity extraction tests with a fixed "today" |
| `test_intents.py` | Intent tests, including that every ordinary question stays a faq |
| `test_dialog.py` | Scripted multi-turn conversations with a fake model that records its calls |
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
- **Hands off to a human:** custom quotes, confirming a specific date's availability, contract and legal questions, and requests to speak to a person are caught by the `handoff` intent. It returns a fixed message and never calls the model, so the hand-off cannot be improvised away.

## Privacy and disclosure

The page states that visitors are talking to software, and that their question is sent to a third-party AI service (Groq). The app does not store conversations, and the notice asks visitors not to type personal or payment information.

## Bias and phrasing

`test_phrasing.py` asks the same question formally, casually, and in different dialects (for example "how long you playin" and "yo how much down payment to lock in the band"). Early runs showed casual wording retrieving the wrong chunk, so the chunks now include everyday synonyms such as "down payment" and "out of town". Known remaining limit: very loose phrasing can still miss, for example "what if my party is out of town, extra cost?" retrieves the cancellation policy.

## Source attribution

Every answer is shown with the source label(s) of the chunk(s) it was
grounded in (e.g. "Booking Policy"), displayed as a caption under the
response, next to the intent that handled the message. A computed travel
quote or booking check cites the policy chunk its numbers came from.
Questions for more details and hand-offs have nothing to attribute, so
they show no source.

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
| 1 | Do you take requests for country songs? | event_types (0.118), genres_style (0.114) | I do not have that information about booking Moments Notice. Please reach out to the band directly for details. | Yes |
| 2 | Can I pay the deposit with a credit card? | deposit_policy (0.210) | I do not have that information about booking Moments Notice. Please reach out to the band directly for details. | Yes |
| 3 | Do you provide catering or a DJ in between sets? | set_length (0.106) | TODO paste the bot's reply here | TODO |
| 4 | Is there a discount for booking multiple events? | advance_booking (0.140) | TODO paste the bot's reply here | TODO |
| 5 | Can you learn a special song for our first dance? | event_types (0.118), genres_style (0.114) | TODO paste the bot's reply here | TODO |

**Result so far (rows 1 and 2):** both returned the exact fixed refusal
sentence. Retrieval found a related chunk each time (the credit card
question pulled the deposit policy), so the model was called and the
refusal came from the grounding prompt holding, not from the threshold
or the chunk wording. Rows 3 to 5: TODO add the same judgment after
pasting the real replies. The scores above were re-run after the chunk
wording changed, so they differ slightly from earlier runs.

## Retest: the deposit question

The first live test of "How much is the deposit?" returned "The deposit
is 30 percent of the total booking fee." The reference text says a 30
percent deposit is required but never says 30 percent *of what*, so
"of the total booking fee" is a detail the model added. After adding a
prompt rule against saying what a number applies to, the retest returned
"The deposit required is 30 percent of the booking fee." The word
"total" is gone but the added "of the booking fee" is still there, so
the prompt rule did not fully fix it. **Status: open.** The cause is
that the knowledge chunk is ambiguous, and a prompt cannot reliably stop
a model from filling an obvious gap. The likely fix is to state in
`knowledge.py` what the 30 percent is calculated on, then retest.

That answer also did not mention the deposit being non-refundable. That
is expected, not a defect: the question asked only for the amount, and
the prompt limits answers to under three sentences. Refundability is
tested by its own question in `TRANSCRIPT_TESTS.md`.
