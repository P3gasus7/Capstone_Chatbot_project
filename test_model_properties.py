"""
CSC-128 Capstone: model-output property tests
Shawn Canady

Model wording changes every run, so these tests never compare exact
strings. They check properties that must hold for any acceptable answer:
it is not blank, it is short, it contains no number that is missing from
the retrieved text, and out-of-scope questions get the refusal.

Run offline (checks the property checkers themselves, no key needed):
    python test_model_properties.py
Run live against Groq (needs GROQ_API_KEY in the environment):
    GROQ_API_KEY=your-key python test_model_properties.py --live
"""
import os
import re
import sys

import grounded_bot as bot
from retriever import Retriever

IN_SCOPE = [
    "How much deposit do I need to pay to book you?",
    "How far in advance should I book you for a wedding?",
    "Do you bring your own sound equipment?",
    "How long do you play for?",
]
# Close to the topic but not answered by any chunk: must refuse.
NEAR_MISS = [
    "Can I pay the deposit with a credit card?",
    "Is there a discount for booking multiple events?",
]
# Unrelated: must refuse (from code, without the model).
OUT_OF_SCOPE = ["How do I pay my college tuition?", "What is the capital of France?"]

NUMBER_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
                "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10"}


def numbers_in(text):
    """Digits and spelled-out small numbers, normalized to digits."""
    found = set(re.findall(r"\d+", text))
    for word in re.findall(r"[a-z]+", text.lower()):
        if word in NUMBER_WORDS:
            found.add(NUMBER_WORDS[word])
    return found


def sentence_count(text):
    return len([s for s in re.split(r"[.!?]+", text) if s.strip()])


def check_answer(answer, context):
    """Return a list of property violations (empty list means all good)."""
    problems = []
    if not answer or not answer.strip():
        problems.append("blank answer")
        return problems
    if sentence_count(answer) > 4:  # prompt says under 3; allow 1 spare
        problems.append("too long ({} sentences)".format(sentence_count(answer)))
    invented = numbers_in(answer) - numbers_in(context)
    if invented:
        problems.append("numbers not in reference text: {}".format(sorted(invented)))
    return problems


def self_check():
    """Prove the checkers catch what they claim to, without any model."""
    ctx = "A 30 percent deposit is due within seven days."
    assert check_answer("You pay a 30 percent deposit within seven days.", ctx) == []
    assert check_answer("The deposit is 50 percent.", ctx)       # invented number
    assert check_answer("   ", ctx)                              # blank
    assert check_answer("One. Two. Three. Four. Five. Six.", ctx)  # too long
    print("[PASS] property checkers catch blank, long, and invented-number answers")


def live_run():
    client = bot.make_client(os.environ["GROQ_API_KEY"])
    retriever = Retriever()
    failures = 0
    for q in IN_SCOPE:
        hits = retriever.search(q)
        text, sources, ok = bot.answer(q, retriever, client)
        problems = [] if not ok else check_answer(text, retriever.build_context(hits))
        problems += [] if ok else ["system failure: " + text]
        failures += bool(problems)
        print("[{}] in scope: {}\n    {}".format("FAIL" if problems else "PASS", q, problems or text))
    for q in NEAR_MISS + OUT_OF_SCOPE:
        text, sources, ok = bot.answer(q, retriever, client)
        refused = text == bot.REFUSAL
        failures += not refused
        print("[{}] must refuse: {}\n    {}".format("PASS" if refused else "FAIL", q, text))
    print("\n{} failure(s). Paste any FAIL into the README table and fix it.".format(failures))


if __name__ == "__main__":
    self_check()
    if "--live" in sys.argv:
        live_run()
