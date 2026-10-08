"""
CSC-128 Capstone: conversation tests (slot filling and state)
Shawn Canady

Run with: python test_dialog.py   (no API key needed)

Each test is a scripted multi-turn conversation. A fake model client
records every call, so the tests can prove that the deterministic
intents never touch the model, and that state carries from turn to turn.
"""
from datetime import date

import groq
import httpx

import dialog
import grounded_bot as bot
from dialog import DialogState, handle_turn
from retriever import Retriever

TODAY = date(2026, 10, 7)
RETRIEVER = Retriever()


class FakeClient:
    """Stands in for Groq. Records each call; returns canned text."""

    def __init__(self, text="The deposit is 30 percent.", error=None):
        self.text, self.error, self.calls = text, error, []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs["messages"][-1]["content"])
        if self.error:
            raise self.error
        message = type("M", (), {"content": self.text})
        choice = type("C", (), {"message": message})
        return type("R", (), {"choices": [choice]})


def conversation(turns, client=None):
    """Run a list of messages through one DialogState; return the replies."""
    state, client = DialogState(), client or FakeClient()
    replies = [handle_turn(t, state, RETRIEVER, client, TODAY) for t in turns]
    return replies, state, client


FAILURES = []


def check(name, condition, detail=""):
    print("[{}] {}".format("PASS" if condition else "FAIL", name))
    if not condition:
        FAILURES.append(name)
        if detail:
            print("      " + detail)


def test_travel_two_turns():
    r, state, client = conversation(
        ["How much would travel cost for my event?", "about 40 miles"])
    check("travel: first turn asks for miles", "How many miles" in r[0].text and r[0].intent == "travel_quote")
    check("travel: 40 miles -> $60 (15 extra x 2 x $2)", "$60" in r[1].text, r[1].text)
    check("travel: quote cites its policy chunk", r[1].sources == ["Booking Policy (travel_fee)"])
    check("travel: model never called", client.calls == [])
    check("travel: flow is closed afterwards", state.intent is None and state.slots == {})


def test_travel_one_shot_and_edges():
    r, _, client = conversation(["What would travel cost for 60 miles?"])
    check("travel: one-shot 60 miles -> $140", "$140" in r[0].text, r[0].text)
    r, _, _ = conversation(["travel cost for 20 miles"])
    check("travel: inside 25 miles -> no fee", "no travel fee" in r[0].text, r[0].text)
    r, _, _ = conversation(["travel cost for 25 miles"])
    check("travel: exactly 25 miles -> no fee", "no travel fee" in r[0].text)
    r, _, _ = conversation(["travel cost for 25.5 miles"])
    check("travel: 25.5 miles -> $2", "$2 " in r[0].text or "= $2." in r[0].text, r[0].text)
    r, _, _ = conversation(["How much would travel cost?", "40"])
    check("travel: bare number accepted after being asked", "$60" in r[1].text, r[1].text)
    r, _, _ = conversation(["How much would travel cost?", "June 14"])
    check("travel: a date is not mistaken for miles", "How many miles" in r[1].text and "$" not in r[1].text, r[1].text)


def test_booking_flow():
    r, state, client = conversation(
        ["I want to book you for my wedding", "October 3, 2027"])
    check("booking: first turn asks for the date (type already known)",
          "What date" in r[0].text and state.slots == {}, r[0].text)
    check("booking: peak wedding date far enough out",
          "at least three months in advance" in r[1].text and "far enough out" in r[1].text, r[1].text)
    check("booking: cites advance booking and deposit chunks",
          r[1].sources == ["Booking Policy (advance_booking)", "Booking Policy (deposit_policy)"])
    check("booking: model never called", client.calls == [])

    r, _, _ = conversation(["I want to book you for my wedding on November 7"])
    check("booking: peak date under three months -> reach out right away",
          "closer than that" in r[0].text and "right away" in r[0].text, r[0].text)

    r, state, _ = conversation(["Can I book you for June 14?", "a corporate event"])
    check("booking: date given first, then asks the event type",
          "What kind of event" in r[0].text and "one event per date" in r[1].text, r[1].text)

    r, _, _ = conversation(["I want to book you for my wedding", "no idea"])
    check("booking: unreadable answer is re-asked", r[1].text.startswith("I didn't catch that."), r[1].text)


def test_past_date():
    r, state, _ = conversation(
        ["I want to book you for my wedding", "March 3, 2025", "March 3, 2027"])
    check("past date: rejected and still asking for a date",
          dialog.MSG_PAST_DATE in r[1].text and state.intent is None, r[1].text)
    check("past date: a later valid date completes the flow",
          "your wedding on Wednesday, March 3, 2027" in r[2].text, r[2].text)


def test_state_survives_side_question():
    client = FakeClient("The deposit is 30 percent.")
    r, state, _ = conversation(
        ["How much would travel cost?", "How much is the deposit?", "30 miles"], client)
    check("state: side question answered by the model", r[1].text.startswith("The deposit is 30 percent.") and len(client.calls) == 1)
    check("state: flow is picked back up with a reminder", "Back to your travel quote: How many miles" in r[1].text, r[1].text)
    check("state: flow still completes afterwards", "$20" in r[2].text, r[2].text)
    check("state: side-question answer keeps its source", r[1].sources == ["Booking Policy (deposit_policy)"])


def test_switching_cancelling_giving_up():
    r, state, client = conversation(
        ["How much would travel cost?", "Can you give me a custom quote?"])
    check("switch: hand-off request mid-flow closes the flow",
          r[1].text == dialog.MSG_HANDOFF and state.intent is None and client.calls == [])

    r, state, _ = conversation(["I want to book you for my wedding", "never mind"])
    check("cancel: 'never mind' drops the flow", r[1].text == dialog.MSG_CANCELLED and state.intent is None)

    r, state, _ = conversation(["How much would travel cost?", "banana", "banana"])
    check("give up: first miss re-asks", r[1].text.startswith("I didn't catch that."))
    check("give up: second miss ends the flow", r[2].text == dialog.MSG_GIVE_UP and state.intent is None)

    r, state, _ = conversation(["How much would travel cost?", "Actually I want to book you for my wedding"])
    check("switch: asking for a different flow restarts cleanly",
          state.intent == "booking_check" and "What date" in r[1].text, r[1].text)


def test_followup_memory():
    client = FakeClient("You pay the deposit within seven days.")
    r, state, _ = conversation(["How much is the deposit?", "And when do I pay it?"], client)
    check("follow-up: model called for both turns", len(client.calls) == 2)
    check("follow-up: model is told what 'it' refers to",
          "How much is the deposit?" in client.calls[1], client.calls[1])
    check("follow-up: answer cites the deposit chunk", r[1].sources == ["Booking Policy (deposit_policy)"], str(r[1].sources))

    r, _, client = conversation(["And when do I pay it?"])
    check("follow-up: with nothing to refer to, refuses without the model",
          r[0].text == bot.REFUSAL and client.calls == [])


def test_handoff_and_scope():
    for text in ["Can you give me legal advice about my venue contract?",
                 "Can you give me a custom quote for a 6 hour event?",
                 "Are you available on June 14?"]:
        r, _, client = conversation([text])
        check("hand-off: {!r}".format(text), r[0].text == dialog.MSG_HANDOFF and r[0].intent == "handoff" and client.calls == [])
    r, _, client = conversation(["What's the weather today?"])
    check("scope: unrelated question refused from code", r[0].text == bot.REFUSAL and client.calls == [])


def test_degraded_modes():
    state = DialogState()
    reply = handle_turn("travel cost for 40 miles", state, RETRIEVER, None, TODAY)
    check("no API key: deterministic intents still work", "$60" in reply.text and reply.ok)
    reply = handle_turn("How much is the deposit?", state, RETRIEVER, None, TODAY)
    check("no API key: faq reports the setup problem", reply.text == bot.MSG_AUTH and not reply.ok)

    err = groq.RateLimitError("x", response=httpx.Response(429, request=httpx.Request("POST", "https://x")), body=None)
    r, _, _ = conversation(["How much is the deposit?"], FakeClient(error=err))
    check("rate limit inside the dialog is still a plain message", r[0].text == bot.MSG_RATE_LIMIT and not r[0].ok)

    r, _, _ = conversation(["   "])
    check("empty message", r[0].text == bot.MSG_EMPTY)
    r, _, _ = conversation(["deposit " * 200])
    check("overlong message", r[0].text == bot.MSG_TOO_LONG)


def run():
    for test in (test_travel_two_turns, test_travel_one_shot_and_edges, test_booking_flow,
                 test_past_date, test_state_survives_side_question,
                 test_switching_cancelling_giving_up, test_followup_memory,
                 test_handoff_and_scope, test_degraded_modes):
        test()
    print("\n{} failure(s)".format(len(FAILURES)))
    assert not FAILURES, "Failed: " + "; ".join(FAILURES)


if __name__ == "__main__":
    run()
