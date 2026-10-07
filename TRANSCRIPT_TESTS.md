# Scripted Transcript Tests

Run by hand on the **live deployed app** with a fresh browser tab. For each
turn, type the message, then tick the checklist. Record what the bot
actually said. The bot has no memory between turns by design, so each turn
is judged on its own.

## Transcript 1 — a normal booking conversation

| Turn | You type | Must be true | Actual reply | Pass? |
|---|---|---|---|---|
| 1 | How much is the deposit? | States 30 percent, mentions non-refundable. Source caption shows Booking Policy. | TODO | TODO |
| 2 | And when do I pay it? | Answers from the same policy (seven days) or refuses cleanly. Never invents a date. | TODO | TODO |
| 3 | What if I cancel? | Mentions 30 days and rebooking vs. forfeit. Source shown. | TODO | TODO |
| 4 | do u travel out of town | Mentions free within 25 miles and the per-mile fee. | TODO | TODO |
| 5 | Do you accept PayPal? | Refuses with the band-contact sentence. No invented payment methods. | TODO | TODO |

## Transcript 2 — scope, failure, and hand-off

| Turn | You type | Must be true | Actual reply | Pass? |
|---|---|---|---|---|
| 1 | Can you give me legal advice about my venue contract? | Refuses and points to the band or a lawyer. No source caption. | TODO | TODO |
| 2 | (send an empty message / spaces) | Asks for a question. No traceback. | TODO | TODO |
| 3 | What's the weather on my wedding day? | Refuses without calling the model (no source caption). | TODO | TODO |
| 4 | Can you give me a custom quote for a 6 hour event? | Refuses and directs to the band (hand-off). Never invents a price. | TODO | TODO |
| 5 | (run locally with a bad key in secrets.toml) any question | Plain "not set up correctly" message in a warning box. No traceback. | TODO | TODO |

## After each run
- Any invented number, price, or policy is a **FAIL**. Note whether a source caption was shown: yes means a prompt problem, no means a retrieval problem.
- Copy real failures into the design document's "three failures" section.
