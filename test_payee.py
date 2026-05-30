"""Unit tests for lib/payee.py rule-based clean-up.

Run directly (no dependencies):   python3 test_payee.py
Or with pytest:                    pytest test_payee.py
"""
from lib.payee import clean_rules, city_from_description


# (display_name, card description or None, expected payee) -- the descriptions
# are real bunq card descriptors captured from payments on 2026-05-29.
CASES = [
    ("Baylings",                "Baylings LEEUWARDEN, NL\n",                 "Baylings"),
    ("ZEEMAN LEEUWARDEN NWE",   "ZEEMAN LEEUWARDEN NWE LEEUWARDEN, NL",      "ZEEMAN"),
    ("HEMA EV0027",             "HEMA EV0027 Leeuwarden, NL",                "HEMA"),
    ("BCK*PiNutsBV",            "BCK*PiNutsBV BROEK OP LANG, NL",            "PiNutsBV"),
    ("CCV*GEBAKSKRAAM DE VRI",  "CCV*GEBAKSKRAAM DE VRI LEEUWARDEN, NL",     "GEBAKSKRAAM DE VRI"),
    ("BCK*Lahore Catering",     "BCK*Lahore Catering Stiens, NL",           "Lahore Catering"),
    ("BCK*De Landheer t stoe",  "BCK*De Landheer t stoe Anjum, NL",         "De Landheer t stoe"),
    ("BCK*Huiskamer MP 0172",   "BCK*Huiskamer MP 0172 MEPPEL, NL",         "Huiskamer"),
    # iDEAL payment request (not a card payment, so no city)
    ("U. Metselaar via Rabo Betaalverzoek", None,                           "U. Metselaar"),
]

CITY_CASES = [
    ("Baylings LEEUWARDEN, NL\n", "LEEUWARDEN"),
    ("HEMA EV0027 Leeuwarden, NL", "Leeuwarden"),
    ("BCK*PiNutsBV BROEK OP LANG, NL", "LANG"),
    ("NL62RABO0377212830 U. Metselaar:High Tea", None),
    (None, None),
]


def test_clean_rules():
    for display_name, description, expected in CASES:
        city = city_from_description(description)
        got = clean_rules(display_name, city=city)
        assert got == expected, \
            "{!r} (city {!r}) -> {!r}, expected {!r}".format(
                display_name, city, got, expected)


def test_city_from_description():
    for description, expected in CITY_CASES:
        got = city_from_description(description)
        assert got == expected, \
            "{!r} -> {!r}, expected {!r}".format(description, got, expected)


def test_never_empty():
    # A descriptor that is nothing but a stripped prefix must not vanish.
    assert clean_rules("BCK*")
    assert clean_rules("") == ""
    assert clean_rules(None) is None


def test_legacy_dash_split():
    assert clean_rules("Jane Doe - thank you") == "Jane Doe"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS {}".format(name))
            except AssertionError as e:
                failures += 1
                print("FAIL {}: {}".format(name, e))
    # Show the before/after table for the captured May 29 payments.
    print("\nBefore -> after (rules):")
    for display_name, description, _ in CASES:
        city = city_from_description(description)
        print("  {:<38} -> {}".format(display_name, clean_rules(display_name, city=city)))
    raise SystemExit(1 if failures else 0)
