"""
CSC-128 Capstone: Moments Notice booking assistant
Shawn Canady

Each entry is one self-contained fact the bot may need, written the way
a visitor would actually ask about it rather than in formal policy
language. Every chunk has an id (for testing and attribution) and a
source label (shown to the user alongside the answer).
"""

DOCUMENTS = [
    {
        "id": "deposit_policy",
        "source": "Booking Policy",
        "text": (
            "Booking Moments Notice requires a 30 percent deposit, paid "
            "within seven days of confirming your date, to hold the date "
            "on the calendar. This deposit is also called a down payment: it is "
            "the money you put down to reserve the date. The deposit is non-refundable. The "
            "remaining balance is due on the day of the performance."
        ),
    },
    {
        "id": "cancellation_policy",
        "source": "Booking Policy",
        "text": (
            "If you need to cancel, events cancelled more than 30 days "
            "before the date can rebook for a different date at no extra "
            "cost. Events cancelled within 30 days of the date forfeit "
            "the deposit, since that date can no longer be rebooked to "
            "another client."
        ),
    },
    {
        "id": "travel_fee",
        "source": "Booking Policy",
        "text": (
            "Moments Notice travels for free within 25 miles of "
            "Charlotte, North Carolina. Events further away, or out of town, "
            "are charged a travel fee of two dollars per mile, round trip, "
            "beyond that 25 mile radius."
        ),
    },
    {
        "id": "advance_booking",
        "source": "Booking Policy",
        "text": (
            "Moments Notice can only accept one event per date, so "
            "popular dates such as spring and fall wedding weekends "
            "should be booked at least three months in advance to "
            "guarantee availability."
        ),
    },
    {
        "id": "equipment_provided",
        "source": "Performance Details",
        "text": (
            "Moments Notice brings its own PA system, wireless "
            "microphones, and basic stage lighting to every performance, "
            "so the venue does not need to provide sound equipment "
            "unless a client specifically asks for something different."
        ),
    },
    {
        "id": "genres_style",
        "source": "Performance Details",
        "text": (
            "Moments Notice plays smooth jazz and R&B music, mixing "
            "original songs with covers of artists such as Anita Baker, "
            "Sade, and Boyz II Men. The band can play more upbeat or more "
            "mellow depending on the event."
        ),
    },
    {
        "id": "event_types",
        "source": "Performance Details",
        "text": (
            "Moments Notice regularly performs at weddings, corporate "
            "events, private parties, and small festivals, adjusting "
            "volume and song selection to fit the occasion, such as "
            "background music during dinner versus a livelier set later "
            "in the evening."
        ),
    },
    {
        "id": "set_length",
        "source": "Performance Details",
        "text": (
            "A standard booking runs 90 minutes total, about an hour and a half "
            "on stage: two 45 minute sets with a 15 minute break in between. Moments Notice can "
            "play a longer show for an additional fee if you want the "
            "band on stage longer than the standard 90 minutes."
        ),
    },
    {
        "id": "arrival_setup",
        "source": "Performance Details",
        "text": (
            "Moments Notice arrives one hour before the performance "
            "start time to set up sound equipment and run a quick "
            "soundcheck, so the venue should have the performance area "
            "accessible by then."
        ),
    },
]
