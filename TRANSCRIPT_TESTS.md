# Scripted Transcript Tests

Run by hand on the **live deployed app** with a fresh browser tab. For each
turn, type the message, then tick the checklist. Record what the bot
actually said. The bot remembers context within one chat session, so run
each transcript in order, in a fresh tab, without reloading in between.

How to read the caption under each reply: it names the intent that handled
the message (faq, travel quote, booking check, or handoff) and, when
there is one, the source. A normal answer shows the chunk it came from; a
refusal, a question for more details, and a hand-off never show a source,
because they have nothing to attribute.

## Transcript 1 — a normal booking conversation

| Turn | You type | Must be true | Actual reply | Pass? |
|---|---|---|---|---|
| 1 | How much is the deposit? | States 30 percent. Caption shows Booking Policy (deposit_policy). Does not add what the 30 percent is "of", since the reference does not say. | The deposit required is 30 percent of the booking fee. | PARTIAL: states 30 percent, but adds "of the booking fee" (see notes) |
| 2 | Is the deposit refundable? | States it is non-refundable. Caption shows Booking Policy (deposit_policy). | TODO | TODO |
| 3 | When is the deposit due? | Says within seven days of confirming the date. Caption shows Booking Policy (deposit_policy). | TODO | TODO |
| 4 | And when do I pay it? | Follow-up memory: "it" is understood as the deposit from turn 3. Says within seven days of confirming the date. Caption shows Booking Policy (deposit_policy). | TODO | TODO |
| 5 | What if I cancel? | Mentions 30 days, rebooking versus forfeiting the deposit. Caption shows Booking Policy (cancellation_policy). | TODO | TODO |
| 6 | do u travel out of town | Free within 25 miles of Charlotte, then two dollars per mile round trip. Caption shows Booking Policy (travel_fee). | TODO | TODO |
| 7 | Do you accept PayPal? | Refuses with the band-contact sentence. No invented payment methods. No caption. | TODO | TODO |

**Notes on turn 1.** The answer states the correct number (pass). It also
adds "of the booking fee", which the reference text never says (the same
issue as the earlier "total booking fee" answer, now without "total").
It did not mention "non-refundable", which is fine: the question asked
only for the amount, and answers are limited to under three sentences.
That fact is checked by turn 2 instead. TODO confirm on screen that the
caption "Source: Booking Policy (deposit_policy)" appeared under this
answer, then delete this sentence.

## Transcript 2 — scope, failure, and hand-off

| Turn | You type | Must be true | Actual reply | Pass? |
|---|---|---|---|---|
| 1 | Can you give me legal advice about my venue contract? | Hand-off: a fixed message sending contract questions to the band. Caption says Intent: handoff, no source. | TODO | TODO |
| 2 | (paste a block of text longer than 500 characters) | A warning box says the question is too long and asks for a shorter one. No traceback. | TODO | TODO |
| 3 | What's the weather today? | Refuses from code, model not called. Caption says Intent: faq with no source. | TODO | TODO |
| 4 | What's the weather on my wedding day? | Refuses. The words "wedding" and "day" match some chunks, so the model is called and the grounding prompt must hold. No caption. | TODO | TODO |
| 5 | Can you give me a custom quote for a 6 hour event? | Hand-off: the same fixed message sending custom quotes to the band. Caption says Intent: handoff. Never invents a price. | TODO | TODO |
| 6 | (run locally with a wrong key in secrets.toml) any question | Plain "not set up correctly" message in a warning box. No traceback. | TODO | TODO |

An empty message cannot be sent from the page, because Streamlit's chat
box ignores blank input. That case is covered by `test_bot.py` ("empty
question").

## Transcript 3 — slot filling and conversation state

Run these in order in one fresh tab. Booking dates use explicit years in
the future so the results do not depend on the day you run them. The
same conversations are tested with a fixed date in `test_dialog.py`.

| Turn | You type | Must be true | Actual reply | Pass? |
|---|---|---|---|---|
| 1 | How much would travel cost for my event? | Asks how many miles from Charlotte. Caption says Intent: travel quote, no source. | TODO | TODO |
| 2 | 40 | Quote with the arithmetic: 15 miles x 2 (round trip) x $2 per mile = $60, and asks you to confirm with the band. Caption cites Booking Policy (travel_fee). | TODO | TODO |
| 3 | I want to book you for my wedding | Remembers the event type, asks only for the date. Caption says Intent: booking check. | TODO | TODO |
| 4 | How much is the deposit? | A side question in the middle of the flow: answers the deposit question (faq, deposit_policy), then adds "Back to your booking check" and repeats the date question. | TODO | TODO |
| 5 | October 3, 2028 | Completes the check: a popular fall wedding date that is far enough out. Mentions the 30 percent deposit. Caption cites advance_booking and deposit_policy. | TODO | TODO |
| 6 | How much would travel cost? | Starts a new travel quote and asks for miles (the earlier flow is finished). | TODO | TODO |
| 7 | banana | Says it didn't catch that and asks for miles again. | TODO | TODO |
| 8 | banana | Gives up after two unreadable answers and sends you to the band. | TODO | TODO |
| 9 | I want to book you for my wedding | Asks for the date. | TODO | TODO |
| 10 | March 3, 2020 | Says the date has already passed and asks for a future date. | TODO | TODO |
| 11 | never mind | Drops the flow with a friendly message. | TODO | TODO |
| 12 | Can I book you for June 14? | Takes the date, then asks what kind of event it is. | TODO | TODO |
| 13 | a corporate event | Completes with the one-event-per-date guidance and the deposit note (not a peak wedding date). | TODO | TODO |

## After each run
- Any invented number, price, or policy is a **FAIL**.
- If a wrong detail appears in an answer whose caption names the **right** chunk, the cause is the prompt. If the caption names the **wrong** chunk, the cause is retrieval.
- Copy real failures into the design document's "three failures" section.
