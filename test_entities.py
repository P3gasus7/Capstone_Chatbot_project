"""
CSC-128 Capstone: entity extraction tests
Shawn Canady

Run with: python test_entities.py   (no API key needed)
Dates use a fixed "today" so the results never change.
"""
from datetime import date

from entities import extract_date, extract_event_type, extract_miles

TODAY = date(2026, 10, 7)

MILES = [
    ("about 40 miles", False, 40),
    ("I'm 12.5 mi away", False, 12.5),
    ("it is 1,000 miles", False, 1000),
    ("40", True, 40),                  # bare number, but we just asked
    ("40", False, None),               # bare number with no question asked
    ("5000 miles", False, None),       # beyond MAX_MILES: a typo
    ("June 14", False, None),
    ("no idea", True, None),
]
TYPES = [
    ("my wedding", "wedding"), ("the reception", "wedding"),
    ("a corporate gig", "corporate event"), ("company picnic", "corporate event"),
    ("a birthday party", "private party"), ("graduation", "private party"),
    ("a street festival", "small festival"),
    ("a corporate party", "corporate event"),   # broad "party" checked last
    ("weddings", "wedding"),
    ("something else", None),
]
DATES = [
    ("June 14", date(2027, 6, 14)),            # no year: next June 14
    ("October 7", date(2026, 10, 7)),          # today counts, not next year
    ("October 6", date(2027, 10, 6)),          # yesterday: roll to next year
    ("June 14th, 2027", date(2027, 6, 14)),
    ("14 June", date(2027, 6, 14)),
    ("the 3rd of March, 2028", date(2028, 3, 3)),
    ("6/14", date(2027, 6, 14)),
    ("6/14/2027", date(2027, 6, 14)),
    ("6/14/27", date(2027, 6, 14)),
    ("2027-06-14", date(2027, 6, 14)),
    ("sept 3", date(2027, 9, 3)),
    ("Feb 30", None),                          # impossible date
    ("13/45/2027", None),
    ("may I book you", None),                  # "may" the word, not the month
    ("no date here", None),
]


def run():
    failed = total = 0

    def check(label, got, expected):
        nonlocal failed, total
        total += 1
        ok = got == expected
        failed += not ok
        print("[{}] {} -> {!r} (expected {!r})".format("PASS" if ok else "FAIL", label, got, expected))

    for text, expecting, expected in MILES:
        check("miles {!r} expecting={}".format(text, expecting), extract_miles(text, expecting), expected)
    for text, expected in TYPES:
        check("type {!r}".format(text), extract_event_type(text), expected)
    for text, expected in DATES:
        check("date {!r}".format(text), extract_date(text, TODAY), expected)

    print("\n{}/{} passed".format(total - failed, total))
    assert failed == 0, "Some entity tests failed."


if __name__ == "__main__":
    run()
