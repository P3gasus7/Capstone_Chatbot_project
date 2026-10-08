"""
CSC-128 Capstone: intent classification
Shawn Canady

Four intents, chosen by plain pattern rules rather than by the model, so
the routing decision is repeatable and can be unit-tested exactly
(see test_intents.py). Rules are checked in a fixed order.

    handoff        custom quotes, contracts, legal questions, date
                   confirmation: things the band must answer itself
    travel_quote   needs a distance; computes the travel fee in code
    booking_check  needs an event type and date; checks the advance
                   booking guideline in code
    faq            everything else: retrieval plus the grounded model
"""
import re
from datetime import date

from entities import extract_date, extract_miles

HANDOFF = "handoff"
TRAVEL_QUOTE = "travel_quote"
BOOKING_CHECK = "booking_check"
FAQ = "faq"

_HANDOFF = re.compile(
    r"\b(custom quote|personali[sz]ed quote|price quote|contract|lawyer|"
    r"attorney|legal|negotiat\w*|"
    r"(?:speak|talk) (?:to|with) (?:a |the |someone|somebody)\w*|"
    r"human|real person|"
    r"check (?:your |the )?availability|"
    r"are you (?:available|free|open)|"
    r"is (?:the |my |our )?(?:date|day) (?:open|available|free)|"
    r"(?:available|free) on)\b"
)

_TRAVEL = re.compile(
    r"(travel|mileage|distance|driv\w+).{0,40}"
    r"(cost|quote|estimate|calculat\w*|charge for|fee for)"
    r"|(cost|quote|estimate|calculate|how much).{0,30}(travel|mileage|driv\w+)"
)

_BOOKING = re.compile(
    r"\b((?:i'?d|i would|we'?d|we would) (?:like|love) to book|"
    r"(?:i|we) (?:want|wanna|need|hope) to book|"
    r"(?:can|could) (?:i|we) book|"
    r"book you (?:for|on)|book (?:the band|moments notice)|"
    r"booking (?:my|an|our)|check my date)\b"
)
# "How far in advance should I book you for a wedding?" is a policy
# question, not a booking request, so it stays a faq.
_ADVANCE_QUESTION = re.compile(
    r"how (?:far|early|long|soon|many months)|in advance|ahead of time|"
    r"months ahead|weeks ahead"
)
_EVENT_WORDS = re.compile(r"\b(book|booking|wedding|party|event|gig|perform|play)\b")


def classify_intent(text, today=None):
    """Return one of HANDOFF, TRAVEL_QUOTE, BOOKING_CHECK, FAQ."""
    t = (text or "").lower()
    today = today or date.today()

    if _HANDOFF.search(t):
        return HANDOFF

    if extract_miles(t) is not None or _TRAVEL.search(t):
        return TRAVEL_QUOTE

    if _ADVANCE_QUESTION.search(t):
        return FAQ
    if _BOOKING.search(t):
        return BOOKING_CHECK
    if extract_date(t, today) is not None and _EVENT_WORDS.search(t):
        return BOOKING_CHECK

    return FAQ
