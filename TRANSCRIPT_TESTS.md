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
| 1 | How much is the deposit? | States 30 percent. Caption shows Booking Policy (deposit_policy). Does not add what the 30 percent is "of", since the reference does not say. | The deposit is 30 percent. | Yes | 
| 2 | Is the deposit refundable? | States it is non-refundable. Caption shows Booking Policy (deposit_policy). | The deposit is non‑refundable. | Yes |
| 3 | When is the deposit due? | Says within seven days of confirming the date. Caption shows Booking Policy (deposit_policy). | The deposit is due within seven days of confirming your date | Yes |
| 4 | And when do I pay it? | Follow-up memory: "it" is understood as the deposit from turn 3. Says within seven days of confirming the date. Caption shows Booking Policy (deposit_policy). | The deposit is due within seven days of confirming your date. It is paid to hold the date on the calendar. The remaining balance is then due on the day of the performance. | Yes |
| 5 | What if I cancel? | Mentions 30 days, rebooking versus forfeiting the deposit. Caption shows Booking Policy (cancellation_policy). | If you cancel more than 30 days before the event you can rebook for a different date at no extra cost. If you cancel within 30 days of the date the deposit is forfeited because the date can no longer be rebooked to another client. | Yes |
| 6 | do u travel out of town | Free within 25 miles of Charlotte, then two dollars per mile round trip. Caption shows Booking Policy (travel_fee). | Yes, we do travel out of town. Events beyond 25 miles from Charlotte incur a travel fee of two dollars per mile, round trip, beyond that radius.| Yes |
| 7 | Do you accept PayPal? | Refuses with the band-contact sentence. No invented payment methods. No caption. | I do not have that information about booking Moments Notice. Please reach out to the band directly for details. | Yes |



## Transcript 2 — scope, failure, and hand-off

| Turn | You type | Must be true | Actual reply | Pass? |
|---|---|---|---|---|
| 1 | Can you give me legal advice about my venue contract? | Hand-off: a fixed message sending contract questions to the band. Caption says Intent: handoff, no source. | That one is best answered by the band directly. Custom quotes, confirming a specific date, and contract questions all go through them, so please reach out to the band directly. | Yes |
| 2 | (paste a block of text longer than 500 characters) | A warning box says the question is too long and asks for a shorter one. No traceback. | That question is a bit long for me. Please shorten it to a sentence or two and try again. | Yes |
| 3 | What's the weather today? | Refuses from code, model not called. Caption says Intent: faq with no source. | I do not have that information about booking Moments Notice. Please reach out to the band directly for details. | You |
| 4 | What's the weather on my wedding day? | Refuses. The words "wedding" and "day" match some chunks, so the model is called and the grounding prompt must hold. No caption. | I do not have that information about booking Moments Notice. Please reach out to the band directly for details. | Yes |
| 5 | Can you give me a custom quote for a 6 hour event? | Hand-off: the same fixed message sending custom quotes to the band. Caption says Intent: handoff. Never invents a price. | That one is best answered by the band directly. Custom quotes, confirming a specific date, and contract questions all go through them, so please reach out to the band directly.| Yes |
| 6 | (run locally with a wrong key in secrets.toml) any question | Plain "not set up correctly" message in a warning box. No traceback. | not set up correctly | Yes |

An empty message cannot be sent from the page, because Streamlit's chat
box ignores blank input. That case is covered by `test_bot.py` ("empty
question").

## Transcript 3 — slot filling and conversation state

Run these in order in one fresh tab. Booking dates use explicit years in
the future so the results do not depend on the day you run them. The
same conversations are tested with a fixed date in `test_dialog.py`.

| Turn | You type | Must be true | Actual reply | Pass? |
|---|---|---|---|---|
| 1 | How much would travel cost for my event? | Asks how many miles from Charlotte. Caption says Intent: travel quote, no source. | Moments Notice travels free within 25 miles of Charlotte, NC. At 50 miles you are 25 miles past that, so the travel fee is 25 miles x 2 (round trip) x =
2permile=100. Please confirm the final amount with the band. | Yes |
| 2 | 40 | Quote with the arithmetic: 15 miles x 2 (round trip) x $2 per mile = $60, and asks you to confirm with the band. Caption cites Booking Policy (travel_fee). | Intent: travel quote · Source: Booking Policy (travel_fee) | Yes |
| 3 | I want to book you for my wedding | Remembers the event type, asks only for the date. Caption says Intent: booking check. | What date is your event? (For example: June 14, 2027 or 6/14/2027) | Yes |
| 4 | How much is the deposit? | A side question in the middle of the flow: answers the deposit question (faq, deposit_policy), then adds "Back to your booking check" and repeats the date question. |The deposit is 30 percent.

Back to your booking check: What date is your event? (For example: June 14, 2027 or 6/14/2027)  | Yes |
| 5 | October 3, 2028 | Completes the check: a popular fall wedding date that is far enough out. Mentions the 30 percent deposit. Caption cites advance_booking and deposit_policy. |For your wedding on Tuesday, October 3, 2028 (about 24 months away): popular dates such as spring and fall weddings should be booked at least three months in advance, and your date is far enough out, so reach out soon to hold it. A 30 percent deposit, paid within seven days of confirming your date, holds it.  | Yes|
| 6 | How much would travel cost? | Starts a new travel quote and asks for miles (the earlier flow is finished). | How many miles from Charlotte, NC is your event? (For example: 40 miles) | Yes |
| 7 | banana | Says it didn't catch that and asks for miles again. | I didn't catch that. How many miles from Charlotte, NC is your event? (For example: 40 miles) | Yes |
| 8 | banana | Gives up after two unreadable answers and sends you to the band. | I'm having trouble reading that. Please reach out to the band directly, or ask me again any time.| Yes |
| 9 | I want to book you for my wedding | Asks for the date. | What date is your event? (For example: June 14, 2027 or 6/14/2027) | Yes |
| 10 | March 3, 2020 | Says the date has already passed and asks for a future date. | That date has already passed. Please give me a future date. What date is your event? (For example: June 14, 2027 or 6/14/2027) | Yes |
| 11 | never mind | Drops the flow with a friendly message. | No problem, I've dropped that. What else would you like to know about booking Moments Notice? | Yes |
| 12 | Can I book you for June 14? | Takes the date, then asks what kind of event it is. | What kind of event is it: a wedding, corporate event, private party, or small festival? | Yes |
| 13 | a corporate event | Completes with the one-event-per-date guidance and the deposit note (not a peak wedding date). | For your corporate event on Monday, June 14, 2027 (about 8 months away): Moments Notice can only accept one event per date, so reach out to the band to confirm that date is open. A 30 percent deposit, paid within seven days of confirming your date, holds it. | Yes |


