# Moments Notice — Booking Assistant

**Author:** Shawn Canady — CSC-128 Capstone

## What it does

This is a grounded chatbot for **Moments Notice**, a jazz/R&B band, built
to answer prospective clients' questions about booking the band for an
event. It answers only from a fixed knowledge base (`knowledge.py`) —
deposit and cancellation policy, travel fees, advance booking, equipment,
genres/style, event types, set length, and arrival/setup. If a question
isn't covered by that knowledge base, the bot refuses rather than
guessing.

## How to run it

```bash
pip install -r requirements.txt
streamlit run grounded_bot.py
```

Retrieval tests (no API key required):

```bash
python test_retriever.py
```

## Files

| File | What's in it |
|---|---|
| `knowledge.py` | 9 knowledge chunks, each with an id and source label |
| `retriever.py` | TF-IDF retrieval: stemming, analyzer, threshold-based search |
| `grounded_bot.py` | Streamlit interface, grounding prompt, empty-retrieval short circuit |
| `test_retriever.py` | Retrieval tests for all 9 chunks plus a negative case |
| `.streamlit/secrets.toml` | Local API key — gitignored, never committed |
| `.gitignore` | Lists `.streamlit/secrets.toml` |
| `requirements.txt` | streamlit, groq, scikit-learn, all pinned |

## How the threshold was set

`test_retriever.py` prints the top match and score for 10 test
questions (9 real questions, 1 that's genuinely unrelated). Running it
gave real matches scoring between **0.122 and 0.324**, while an
unrelated question ("How do I pay my college tuition?") scored
**0.0** against every chunk. `DEFAULT_THRESHOLD = 0.10` in
`retriever.py` sits comfortably below every true match and above the
unrelated score, so it was set from that printed evidence rather than
guessed.

## Source attribution

Every answer the bot gives is shown with the source label(s) of the
chunk(s) it was grounded in (e.g. "Booking Policy" or "Performance
Details"), displayed as a caption under the response.

This matters because it lets you tell apart two very different kinds
of failure. If the bot refuses or gives a wrong answer **and no
source is shown**, that's a **retrieval failure** — nothing relevant
was found, so the short circuit fired before the model was ever
called. If the bot gives a wrong or invented answer **while a source
is shown**, that's a **prompt failure** — the retriever found
something relevant, but the model didn't stay inside it. Without
showing sources, both failures would look identical to the user (just
a wrong answer), and there'd be no way to tell whether to fix the
retriever's threshold/chunks or fix the grounding prompt.

## Hallucination testing (five near-miss questions)

These are five questions that are close to the bot's actual topic but
not directly answered by any chunk. For each one, the retriever *did*
find a topically related chunk (so the model was called, not
short-circuited) — meaning the refusal has to come from the grounding
prompt holding, not from retrieval finding nothing.

> **Note:** the "Retrieved chunk" column below is real output from
> `retriever.py`. The "Actual bot response" column needs to be filled
> in by running each question against the deployed app once the Groq
> key is in place, then recorded here before submission — I don't have
> a way to call the Groq API from here to generate that part for you.

| # | Question | Retrieved chunk(s) | Actual bot response | Refused correctly? |
|---|---|---|---|---|
| 1 | Do you take requests for country songs? | event_types (0.118), genres_style (0.114) | _fill in_ | _fill in_ |
| 2 | Can I pay the deposit with a credit card? | deposit_policy (0.179) | _fill in_ | _fill in_ |
| 3 | Do you provide catering or a DJ in between sets? | set_length (0.113) | _fill in_ | _fill in_ |
| 4 | Is there a discount for booking multiple events? | advance_booking (0.140) | _fill in_ | _fill in_ |
| 5 | Can you learn a special song for our first dance? | event_types (0.118), genres_style (0.114) | _fill in_ | _fill in_ |

**If it refused correctly:** say which of the three — threshold,
chunk wording, or prompt — deserves the credit. In this case it's
almost certainly the **grounding prompt**: retrieval intentionally
found a related chunk in every row above, so the model had context in
front of it and had to choose to say "I don't have that information"
rather than use the nearby (but non-answering) context to improvise.

**If it invented something instead:** note that here too, and record
which of the three you changed in response — e.g. tightening a rule
in `GROUNDED_PROMPT` (like adding "do not answer questions the
reference text doesn't directly address"), rewording a chunk, or
raising `DEFAULT_THRESHOLD`.
