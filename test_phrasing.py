"""
CSC-128 Capstone: phrasing tests (bias check)
Shawn Canady

The same question written formally, casually, and in different dialects
should reach the same chunk. If it does not, the bot treats visitors
differently depending on how they write, which is a defect whether or
not it was intended. Run with: python test_phrasing.py (no API key).
"""
from retriever import Retriever

# expected chunk id -> several ways a real visitor might ask for it
VARIANTS = {
    "deposit_policy": [
        "How much deposit do I need to pay to book you?",
        "what's the deposit",
        "how much is the deposit to book y'all",
        "yo how much down payment to lock in the band",
        "How much money do I have to put down to reserve the date?",
    ],
    "travel_fee": [
        "Do you charge extra if the venue is far away?",
        "do u charge for travel",
        "is there an extra charge if the event is out of town",
    ],
    "set_length": [
        "How long do you play for?",
        "how long is the show",
        "how many hours will y'all be on stage",
        "how long you playin",
    ],
}


def run_tests():
    retriever = Retriever()
    total = failed = 0
    for expected, questions in VARIANTS.items():
        for q in questions:
            hits = retriever.search(q)
            got = hits[0][0]["id"] if hits else None
            total += 1
            ok = got == expected
            failed += not ok
            print("[{}] {!r} -> {} (expected {})".format(
                "PASS" if ok else "FAIL", q, got, expected))
    print("\n{}/{} passed".format(total - failed, total))
    assert failed == 0, "Some phrasing variants reached the wrong chunk."


if __name__ == "__main__":
    run_tests()
