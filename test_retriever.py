"""
CSC-128 Assignment 6: retrieval tests
Shawn Canady

Run with: python test_retriever.py
No API key needed -- this only tests the TF-IDF retrieval, not the model.
"""
from retriever import Retriever

# (question, expected chunk id or None if it should retrieve nothing)
TEST_CASES = [
    ("How much deposit do I need to pay to book you?", "deposit_policy"),
    ("What happens if I need to cancel my event?", "cancellation_policy"),
    ("Do you charge extra if the venue is far away?", "travel_fee"),
    ("How far in advance should I book you for a wedding?", "advance_booking"),
    ("Do you bring your own sound equipment?", "equipment_provided"),
    ("What kind of music do you play?", "genres_style"),
    ("Can you perform at a corporate event?", "event_types"),
    ("How long do you play for?", "set_length"),
    ("What time do you arrive to set up?", "arrival_setup"),
    ("How do I pay my college tuition?", None),
]


def run_tests():
    retriever = Retriever()
    passed = 0

    print("Question -> top match (score)\n")
    for question, expected_id in TEST_CASES:
        hits = retriever.search(question)
        top = hits[0] if hits else None
        top_id = top[0]["id"] if top else None
        top_score = round(top[1], 3) if top else 0.0

        ok = top_id == expected_id
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(
            "[{}] \"{}\"\n    got: {} ({})   expected: {}".format(
                status, question, top_id, top_score, expected_id
            )
        )

    print("\n{}/{} passed".format(passed, len(TEST_CASES)))
    assert passed == len(TEST_CASES), "Some retrieval tests failed."


if __name__ == "__main__":
    run_tests()
