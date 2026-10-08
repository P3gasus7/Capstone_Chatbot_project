"""
CSC-128 Capstone: intent classification tests
Shawn Canady

Run with: python test_intents.py   (no API key needed)

Two jobs: each of the four intents is recognized, and, just as
important, every ordinary question the bot already answers stays a faq.
A slot-filling flow that hijacked "How far in advance should I book you
for a wedding?" would break the bot.
"""
from datetime import date

from intents import BOOKING_CHECK, FAQ, HANDOFF, TRAVEL_QUOTE, classify_intent
from test_retriever import TEST_CASES
from test_phrasing import VARIANTS

TODAY = date(2026, 10, 7)

CASES = {
    TRAVEL_QUOTE: [
        "How much would travel cost for my event?",
        "what would the travel cost be for 40 miles",
        "I'm 60 miles away",
        "estimate the travel fee",
        "how much to travel to Raleigh?",
    ],
    BOOKING_CHECK: [
        "I want to book you for my wedding",
        "Can I book you for June 14?",
        "I'd like to book you on 6/14/2027",
        "we want to book the band",
    ],
    HANDOFF: [
        "Can you give me a custom quote for a 6 hour event?",
        "Can you give me legal advice about my venue contract?",
        "Are you available on June 14?",
        "can I speak to a real person",
        "I want to negotiate the price",
    ],
    FAQ: [
        "How far in advance should I book you for a wedding?",
        "do u travel out of town",
        "Do you charge extra if the venue is far away?",
        "is there an extra charge if the event is out of town",
        "What if I cancel?",
        "Do you accept PayPal?",
        "What's the weather today?",
        "Do you take requests for country songs?",
        "Can I pay the deposit with a credit card?",
        "Is there a discount for booking multiple events?",
        "And when do I pay it?",
    ],
}


def run():
    failed = total = 0

    def check(text, expected):
        nonlocal failed, total
        total += 1
        got = classify_intent(text, TODAY)
        ok = got == expected
        failed += not ok
        print("[{}] {!r} -> {} (expected {})".format("PASS" if ok else "FAIL", text, got, expected))

    for expected, texts in CASES.items():
        for text in texts:
            check(text, expected)

    # Every question the retriever and phrasing tests already use is a faq.
    for question, _ in TEST_CASES:
        check(question, FAQ)
    for questions in VARIANTS.values():
        for question in questions:
            check(question, FAQ)

    print("\n{}/{} passed".format(total - failed, total))
    assert failed == 0, "Some intent tests failed."


if __name__ == "__main__":
    run()
