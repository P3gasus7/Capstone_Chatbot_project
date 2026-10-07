# Design Document — Moments Notice Booking Assistant

**Author:** Shawn Canady — CSC-128 Capstone

> Check the assignment page for the exact six section names and rename
> the headings below to match. Everything marked TODO needs your own
> facts; I left it blank rather than invent test results.

## 1. Purpose and audience

The audience is prospective clients (couples, event planners, corporate
organizers) deciding whether and how to book the band Moments Notice.
Their questions are repetitive and factual: how much, how far in
advance, what's included, what happens if I cancel. A bot can answer
these at any hour, and the band keeps control of what is promised
because it can only repeat what is in `knowledge.py`.

## 2. Architecture

- `app.py` — Streamlit interface only.
- `grounded_bot.py` — the decisions: retrieve, refuse or call the model,
  convert failures to messages.
- `retriever.py` — TF-IDF search over the knowledge chunks.
- `knowledge.py` — nine chunks, each with an id and source label.

Flow for one question: validate the text → retrieve chunks above the
threshold → if none, return the fixed refusal → otherwise send the
chunks and the question to the model with a prompt that forbids outside
knowledge → return the answer with its source labels.

The interface and the logic are separate so the logic can be tested
with a fake client (`test_bot.py`) without a browser or API key.

## 3. Where deterministic code was chosen over the model

| Decision | Why code, not the model |
|---|---|
| Refusing when nothing is retrieved | A model given an empty context may improvise despite instructions. Code returns the refusal string and never calls the model, so the outcome can't vary. |
| Choosing what is relevant (TF-IDF + threshold) | Retrieval is a measurable, repeatable step. I set the threshold from printed scores (0.122–0.324 for real questions, 0.0 for unrelated). I can unit-test it exactly, which I cannot do with model output. |
| Error messages | Fixed strings per failure type, so a rate limit always says the same actionable thing and never leaks an exception. |
| Input limits (empty, over 500 characters) | A simple length check is cheaper and safer than asking a model to cope with bad input. |
| Source labels | Come from the retrieved chunks' metadata, not from the model, so the model cannot invent a citation. |

The model is used only for the part code can't do well: phrasing a short,
natural answer from the retrieved text.

## 4. Grounding and refusal

The prompt tells the model to use only the reference text, to answer with
the exact refusal sentence when the answer isn't there, to avoid guessing
numbers, and to stay under three sentences. Because retrieval can return
a related but non-answering chunk (for example, "Can I pay the deposit
by credit card?" retrieves the deposit policy, which doesn't mention
payment methods), the prompt, not retrieval, must hold in those cases.
Section 5 records how that was tested.

## 5. Testing: three failures and what was done

TODO Replace with three real failures from your own testing. Candidates
that match your code's history, to keep only if they actually happened:

1. **Failure:** TODO what you asked and what went wrong.
   **Cause:** retrieval, chunk wording, or prompt (source captions tell you which).
   **Fix:** TODO the change and the retest result.
2. **Failure:** TODO
   **Cause:** TODO
   **Fix:** TODO
3. **Failure:** TODO
   **Cause:** TODO
   **Fix:** TODO

Automated tests: `test_retriever.py` (10/10) covers retrieval and the
threshold; `test_bot.py` (12/12) covers rate limit, connection error,
timeout, bad key, server error, unexpected exception, blank answer,
empty and overlong input, refusal without a model call, and the happy
path.

Property tests (`test_model_properties.py`) check model output without
exact strings: not blank, short, no number absent from the reference
text, and refusal on out-of-scope input. `test_phrasing.py` checks bias:
formal, casual, and dialect phrasings of one question must reach the
same chunk. Scripted transcripts are in `TRANSCRIPT_TESTS.md`.

## 6. Refusal, hand-off, privacy, and disclosure

- **One thing it refuses:** anything not in its knowledge base, including legal or financial advice and prices not stated.
- **One thing it hands to a human:** custom quotes, date availability confirmation, and contracts go to the band.
- **Disclosure:** the page says visitors are talking to software.
- **Privacy:** the question is sent to Groq; the page says so, asks visitors not to enter personal or payment details, and the app does not save conversations.

## 7. Limitations and what I would change

- Retrieval is word-based, so a question phrased with none of the
  chunk's vocabulary can miss. Phrasing tests found this: casual wording
  such as "down payment" first retrieved the wrong chunk, which I fixed by
  adding everyday synonyms to the chunks. "What if my party is out of
  town, extra cost?" still reaches the cancellation chunk. A semantic (embedding) retriever would
  handle paraphrases better.
- The bot has no memory across turns, so a follow-up like "and for
  that?" fails to retrieve anything.
- Knowledge is static; changing prices means editing `knowledge.py` and
  redeploying.
- TODO state the one thing you would change, and say it in your demo too.

