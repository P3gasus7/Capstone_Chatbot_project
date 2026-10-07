"""
CSC-128 Capstone: failure-path tests
Shawn Canady

Run with: python test_bot.py
No API key needed. A fake client stands in for Groq and raises the real
exception classes, so this checks that every failure becomes a readable
message and never a traceback.
"""
import groq
import httpx

import grounded_bot as bot
from retriever import Retriever


def _response(status):
    return httpx.Response(status, request=httpx.Request("POST", "https://x"))


class FakeClient:
    """Mimics client.chat.completions.create(...)."""

    def __init__(self, result=None, error=None):
        self.result, self.error = result, error
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        if self.error:
            raise self.error
        message = type("M", (), {"content": self.result})
        choice = type("C", (), {"message": message})
        return type("R", (), {"choices": [choice]})


GOOD_Q = "How much deposit do I need to pay to book you?"
CASES = [
    ("rate limit", GOOD_Q,
     FakeClient(error=groq.RateLimitError("x", response=_response(429), body=None)),
     bot.MSG_RATE_LIMIT),
    ("connection error", GOOD_Q,
     FakeClient(error=groq.APIConnectionError(request=httpx.Request("POST", "https://x"))),
     bot.MSG_CONNECTION),
    ("timeout", GOOD_Q,
     FakeClient(error=groq.APITimeoutError(request=httpx.Request("POST", "https://x"))),
     bot.MSG_CONNECTION),
    ("bad API key", GOOD_Q,
     FakeClient(error=groq.AuthenticationError("x", response=_response(401), body=None)),
     bot.MSG_AUTH),
    ("server error", GOOD_Q,
     FakeClient(error=groq.InternalServerError("x", response=_response(500), body=None)),
     bot.MSG_UNAVAILABLE),
    ("unexpected exception", GOOD_Q,
     FakeClient(error=ValueError("boom")), bot.MSG_UNAVAILABLE),
    ("blank model answer", GOOD_Q, FakeClient(result="   "), bot.MSG_BLANK_ANSWER),
    ("None model answer", GOOD_Q, FakeClient(result=None), bot.MSG_BLANK_ANSWER),
    ("empty question", "   ", FakeClient(result="unused"), bot.MSG_EMPTY),
    ("overlong question", "deposit " * 200, FakeClient(result="unused"), bot.MSG_TOO_LONG),
]


def run():
    retriever = Retriever()
    failed = 0
    for name, question, client, expected in CASES:
        text, sources, ok = bot.answer(question, retriever, client)
        good = text == expected and not ok and sources == []
        failed += not good
        print("[{}] {}".format("PASS" if good else "FAIL", name))

    # Empty retrieval: must refuse from code WITHOUT touching the model.
    exploding = FakeClient(error=RuntimeError("model must not be called"))
    text, sources, ok = bot.answer("How do I pay my college tuition?", retriever, exploding)
    good = text == bot.REFUSAL and ok and sources == []
    failed += not good
    print("[{}] no retrieval -> refusal, model not called".format("PASS" if good else "FAIL"))

    # Happy path: answer passes through with its sources.
    text, sources, ok = bot.answer(GOOD_Q, retriever, FakeClient(result="30 percent."))
    good = ok and text == "30 percent." and sources and sources[0] == "Booking Policy (deposit_policy)"
    failed += not good
    print("[{}] happy path returns text and top source".format("PASS" if good else "FAIL"))

    total = len(CASES) + 2
    print("\n{}/{} passed".format(total - failed, total))
    assert failed == 0, "Some failure-path tests failed."


if __name__ == "__main__":
    run()
