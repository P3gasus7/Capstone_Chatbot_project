"""
CSC-128 Capstone: conversation logic (intents, slot filling, state)
Shawn Canady

This file is where a visitor's message becomes a reply. It holds the
conversation state across turns and routes each message by intent:

    handoff        fixed message, no model
    travel_quote   asks for the distance, then computes the fee in code
    booking_check  asks for event type and date, then checks the advance
                   booking guideline in code
    faq            retrieval plus the grounded model (grounded_bot.py)

Only the faq path ever calls the model. The two slot-filling flows are
deterministic on purpose: a price or a date comparison must come out the
same every time, which a model cannot promise.

No Streamlit and no Groq in this file, so all of it is unit-tested
without a browser or an API key (see test_dialog.py).
"""
import calendar
import re
from dataclasses import dataclass, field
from datetime import date

import grounded_bot
from entities import extract_date, extract_event_type, extract_miles
from intents import BOOKING_CHECK, FAQ, HANDOFF, TRAVEL_QUOTE, classify_intent
from knowledge import DOCUMENTS

# Policy numbers, copied from knowledge.py's travel_fee chunk. If the
# band changes the policy, change both places.
FREE_RADIUS_MILES = 25
DOLLARS_PER_MILE = 2
ADVANCE_MONTHS = 3
PEAK_WEDDING_MONTHS = (3, 4, 5, 9, 10, 11)  # spring and fall

# Slots each flow must fill, in the order the bot asks for them.
FLOWS = {
    TRAVEL_QUOTE: ["miles"],
    BOOKING_CHECK: ["event_type", "event_date"],
}
FLOW_LABEL = {TRAVEL_QUOTE: "travel quote", BOOKING_CHECK: "booking check"}

PROMPTS = {
    "miles": "How many miles from Charlotte, NC is your event? (For example: 40 miles)",
    "event_type": (
        "What kind of event is it: a wedding, corporate event, private "
        "party, or small festival?"
    ),
    "event_date": "What date is your event? (For example: June 14, 2027 or 6/14/2027)",
}
MSG_HANDOFF = (
    "That one is best answered by the band directly. Custom quotes, "
    "confirming a specific date, and contract questions all go through "
    "them, so please reach out to the band directly."
)
MSG_CANCELLED = (
    "No problem, I've dropped that. What else would you like to know "
    "about booking Moments Notice?"
)
MSG_GIVE_UP = (
    "I'm having trouble reading that. Please reach out to the band "
    "directly, or ask me again any time."
)
MSG_PAST_DATE = "That date has already passed. Please give me a future date."

MAX_MISSES = 2  # unreadable answers in a row before the flow is dropped

_CANCEL = re.compile(r"^\s*(never ?mind|nvm|forget it|start over|stop|cancel)\b")
_QUESTION_START = re.compile(
    r"^\s*(how|what|when|where|why|who|do|does|did|can|could|is|are|will|would)\b"
)
_FOLLOWUP_START = re.compile(r"^\s*(and|also|what about|how about|then|so|but|ok|okay)\b")
_PRONOUN = re.compile(r"\b(it|that|this|those|them|there)\b")


@dataclass
class DialogState:
    """Everything the bot remembers between turns."""
    intent: str = None            # the slot-filling flow in progress, if any
    slots: dict = field(default_factory=dict)
    awaiting: str = None          # the slot the bot last asked for
    misses: int = 0               # unreadable answers to the current question
    last_question: str = None     # last faq question that got a real answer

    def reset_flow(self):
        self.intent, self.slots, self.awaiting, self.misses = None, {}, None, 0


@dataclass
class Reply:
    text: str
    sources: list
    ok: bool
    intent: str = None


# ---------------------------------------------------------------- helpers

def _label(doc_id):
    for doc in DOCUMENTS:
        if doc["id"] == doc_id:
            return "{} ({})".format(doc["source"], doc["id"])
    return doc_id


def add_months(d, months):
    """The date `months` calendar months after d (clamped to month end)."""
    year, month = divmod(d.year * 12 + d.month - 1 + months, 12)
    month += 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _money(amount):
    return "${:,.0f}".format(amount) if amount == int(amount) else "${:,.2f}".format(amount)


def _long_date(d):
    return "{:%A, %B} {}, {}".format(d, d.day, d.year)


def is_followup(text):
    """Short messages like 'And when do I pay it?' that lean on the last topic."""
    t = (text or "").lower()
    return len(t.split()) <= 10 and bool(_FOLLOWUP_START.match(t) or _PRONOUN.search(t))


def _looks_like_question(text):
    return "?" in text or bool(_QUESTION_START.match(text.lower()))


# ------------------------------------------------------ deterministic work

def travel_quote(miles):
    """The travel fee, from the travel_fee policy. Returns the reply text."""
    if miles <= FREE_RADIUS_MILES:
        return (
            "{} miles is within {} miles of Charlotte, NC, so there is no "
            "travel fee.".format(miles, FREE_RADIUS_MILES)
        )
    extra = miles - FREE_RADIUS_MILES
    fee = extra * 2 * DOLLARS_PER_MILE  # round trip, so each extra mile counts twice
    return (
        "Moments Notice travels free within {free} miles of Charlotte, NC. "
        "At {miles} miles you are {extra} miles past that, so the travel "
        "fee is {extra} miles x 2 (round trip) x ${rate} per mile = {fee}. "
        "Please confirm the final amount with the band.".format(
            free=FREE_RADIUS_MILES, miles=miles, extra=extra,
            rate=DOLLARS_PER_MILE, fee=_money(fee),
        )
    )


def booking_check(event_type, event_date, today):
    """The advance-booking guidance, from the advance_booking policy."""
    months_away = max(0, round((event_date - today).days / 30.44))
    peak = event_type == "wedding" and event_date.month in PEAK_WEDDING_MONTHS
    far_enough = event_date >= add_months(today, ADVANCE_MONTHS)

    head = "For your {} on {} (about {} month{} away): ".format(
        event_type, _long_date(event_date), months_away,
        "" if months_away == 1 else "s",
    )
    if peak and far_enough:
        advice = (
            "popular dates such as spring and fall weddings should be booked "
            "at least three months in advance, and your date is far enough out, "
            "so reach out soon to hold it."
        )
    elif peak:
        advice = (
            "popular dates such as spring and fall weddings should be booked "
            "at least three months in advance, and that date is closer than "
            "that, so reach out to the band right away to see if it is still "
            "open."
        )
    else:
        advice = (
            "Moments Notice can only accept one event per date, so reach out "
            "to the band to confirm that date is open."
        )
    tail = (
        " A 30 percent deposit, paid within seven days of confirming your "
        "date, holds it."
    )
    return head + advice + tail


# ----------------------------------------------------------- slot filling

def _fill(state, text, today):
    """
    Try to fill the flow's empty slots from this message. Returns
    (filled_slot_names, problem) where problem is "past_date" if the
    visitor gave a date that has already passed.
    """
    filled, problem = [], None
    date_in_text = extract_date(text, today)

    for slot in FLOWS[state.intent]:
        if slot in state.slots:
            continue
        if slot == "miles":
            # A bare number only counts as miles if we just asked, and
            # never when the number is really part of a date.
            expecting = state.awaiting == "miles" and date_in_text is None
            value = extract_miles(text, expecting=expecting)
        elif slot == "event_type":
            value = extract_event_type(text)
        else:  # event_date
            value = date_in_text
            if value is not None and value < today:
                problem, value = "past_date", None
        if value is not None:
            state.slots[slot] = value
            filled.append(slot)
    return filled, problem


def _advance(state, today, problem=None):
    """Ask for the next missing slot, or finish the flow."""
    intent = state.intent
    for slot in FLOWS[intent]:
        if slot not in state.slots:
            state.awaiting = slot
            prompt = PROMPTS[slot]
            if problem == "past_date" and slot == "event_date":
                prompt = MSG_PAST_DATE + " " + PROMPTS[slot]
            return Reply(prompt, [], True, intent)

    if intent == TRAVEL_QUOTE:
        text = travel_quote(state.slots["miles"])
        sources = [_label("travel_fee")]
    else:
        text = booking_check(state.slots["event_type"], state.slots["event_date"], today)
        sources = [_label("advance_booking"), _label("deposit_policy")]
    state.reset_flow()
    return Reply(text, sources, True, intent)


def _start_flow(intent, text, state, today):
    state.reset_flow()
    state.intent = intent
    _, problem = _fill(state, text, today)
    return _advance(state, today, problem)


# ------------------------------------------------------------------- faq

def _faq(text, state, retriever, client):
    if client is None:
        return Reply(grounded_bot.MSG_AUTH, [], False, FAQ)

    question, search_text, resolved = text, None, False
    if state.last_question and is_followup(text) and not retriever.search(text):
        # "And when do I pay it?" retrieves nothing on its own. Borrow
        # the last topic for retrieval, and tell the model what the
        # follow-up refers to.
        search_text = state.last_question + " " + text
        question = "{} (This follows the visitor's earlier question: {})".format(
            text, state.last_question
        )
        resolved = True

    answer, sources, ok = grounded_bot.answer(question, retriever, client, search_text)
    if ok and sources and not resolved:
        state.last_question = text
    return Reply(answer, sources, ok, FAQ)


# --------------------------------------------------------------- the turn

def handle_turn(text, state, retriever, client, today=None):
    """
    Handle one visitor message. `state` is updated in place and carries
    the conversation to the next turn. `client` may be None (no API key):
    the deterministic intents still work, and only the faq path reports
    the setup problem.
    """
    today = today or date.today()
    text = (text or "").strip()
    if not text:
        return Reply(grounded_bot.MSG_EMPTY, [], False)
    if len(text) > grounded_bot.MAX_QUESTION_CHARS:
        return Reply(grounded_bot.MSG_TOO_LONG, [], False)

    if state.intent and _CANCEL.match(text.lower()):
        state.reset_flow()
        return Reply(MSG_CANCELLED, [], True)

    if state.intent:
        return _continue_flow(text, state, retriever, client, today)

    intent = classify_intent(text, today)
    if intent == HANDOFF:
        return Reply(MSG_HANDOFF, [], True, HANDOFF)
    if intent in FLOWS:
        return _start_flow(intent, text, state, today)
    return _faq(text, state, retriever, client)


def _continue_flow(text, state, retriever, client, today):
    """A slot-filling flow is open: read this message as an answer to it."""
    filled, problem = _fill(state, text, today)
    if filled:
        state.misses = 0
        return _advance(state, today)

    # Not an answer. Maybe the visitor changed their mind about what
    # they want, or asked something else in the middle.
    new_intent = classify_intent(text, today)
    if new_intent == HANDOFF:
        state.reset_flow()
        return Reply(MSG_HANDOFF, [], True, HANDOFF)
    if new_intent in FLOWS and new_intent != state.intent:
        return _start_flow(new_intent, text, state, today)

    if problem is None and _looks_like_question(text):
        # Answer the side question, then pick the flow back up. The
        # slots collected so far are kept.
        reply = _faq(text, state, retriever, client)
        reminder = "Back to your {}: {}".format(
            FLOW_LABEL[state.intent], PROMPTS[state.awaiting]
        )
        return Reply(reply.text + "\n\n" + reminder, reply.sources, reply.ok, reply.intent)

    state.misses += 1
    if state.misses >= MAX_MISSES:
        state.reset_flow()
        return Reply(MSG_GIVE_UP, [], True)
    reply = _advance(state, today, problem)
    if problem is None:
        reply.text = "I didn't catch that. " + reply.text
    return reply
