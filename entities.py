"""
CSC-128 Capstone: entity extraction
Shawn Canady

Plain-code extraction of the three things the bot collects from a
visitor: how far away the event is (miles), what kind of event it is,
and what date it is on. No model is involved, so every function here
can be unit-tested with exact answers (see test_entities.py).
"""
import calendar
import re
from datetime import date

MAX_MILES = 1000  # anything beyond this is a typo, not a booking

# Canonical event type -> words a visitor might use. Order matters:
# "corporate party" should read as corporate, "festival party" as a
# festival, so the broad word "party" is checked last.
EVENT_TYPES = [
    ("wedding", ("wedding", "reception", "marriage", "bride", "groom")),
    ("corporate event", ("corporate", "company", "business", "office",
                         "conference", "work event")),
    ("small festival", ("festival", "fair")),
    ("private party", ("party", "birthday", "anniversary", "graduation",
                       "retirement", "private")),
]

_MONTHS = {}
for _i in range(1, 13):
    _MONTHS[calendar.month_name[_i].lower()] = _i
    _MONTHS[calendar.month_abbr[_i].lower()] = _i
_MONTHS["sept"] = 9

_MONTH_WORD = (
    r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|"
    r"aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
_ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
_SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
_MONTH_FIRST = re.compile(
    r"\b" + _MONTH_WORD + r"\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b"
)
_DAY_FIRST = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?" + _MONTH_WORD + r"\b(?:,?\s+(\d{4}))?"
)


def extract_miles(text, expecting=False):
    """
    Return the distance in miles, or None.

    "40 miles" and "40 mi" always count. A bare number ("about 40") only
    counts when expecting=True, meaning the bot just asked for a
    distance. Otherwise a stray number in an unrelated sentence would be
    mistaken for a distance.
    """
    t = (text or "").lower().replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:miles?|mi)\b", t)
    if not match and expecting:
        match = re.search(r"(?<![\d/.:-])(\d+(?:\.\d+)?)(?![\d/:-])", t)
    if not match:
        return None
    value = float(match.group(1))
    if value > MAX_MILES:
        return None
    return int(value) if value == int(value) else value


def extract_event_type(text):
    """Return a canonical event type, or None."""
    t = (text or "").lower()
    for canonical, words in EVENT_TYPES:
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"s?\b", t):
                return canonical
    return None


def _month_number(word):
    """'june', 'jun', 'sept', and 'sep' all map to a month number."""
    return _MONTHS.get(word) or _MONTHS[word[:3]]


def _build(year, month, day):
    try:
        return date(year, month, day)
    except ValueError:  # Feb 30, month 13, and so on
        return None


def _resolve_year(year_text, month, day, today):
    """No year given: use the next time that month/day comes around."""
    if year_text:
        year = int(year_text)
        return year + 2000 if year < 100 else year
    candidate = _build(today.year, month, day)
    if candidate is not None and candidate < today:
        return today.year + 1
    return today.year


def extract_date(text, today):
    """
    Return a datetime.date, or None.

    Understands "June 14", "June 14th, 2027", "14 June", "6/14",
    "6/14/2027", and "2027-06-14". With no year it picks the next
    occurrence on or after today. Impossible dates return None.
    """
    t = (text or "").lower()

    match = _ISO.search(t)
    if match:
        return _build(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    match = _MONTH_FIRST.search(t)
    if match:
        month, day = _month_number(match.group(1)), int(match.group(2))
        return _build(_resolve_year(match.group(3), month, day, today), month, day)

    match = _DAY_FIRST.search(t)
    if match:
        day, month = int(match.group(1)), _month_number(match.group(2))
        return _build(_resolve_year(match.group(3), month, day, today), month, day)

    match = _SLASH.search(t)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        return _build(_resolve_year(match.group(3), month, day, today), month, day)

    return None
