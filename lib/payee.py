import re

# Clean up the messy merchant descriptors that banks put in the counterparty
# name of card and online payments, e.g.
#
#   "BCK*Lahore Catering"      -> "Lahore Catering"
#   "CCV*GEBAKSKRAAM DE VRI"   -> "GEBAKSKRAAM DE VRI"
#   "HEMA EV0027"              -> "HEMA"
#   "ZEEMAN LEEUWARDEN NWE"    -> "ZEEMAN"      (when city "Leeuwarden" is known)
#   "U. Metselaar via Rabo Betaalverzoek" -> "U. Metselaar"
#
# Everything here is plain string munging with no external dependencies, so it
# can be unit tested in isolation (see test_payee.py).


# Payment service provider prefix, e.g. "BCK*", "CCV*", "ZTL*", "SumUp  *",
# "iZ *", "SQ *", "PP*".  Two to nine leading characters followed by a star.
_PSP_PREFIX = re.compile(r"^\s*[A-Za-z0-9.]{2,9}\s*\*\s*")

# Payment-request boilerplate suffix, e.g. "... via Rabo Betaalverzoek",
# "... via Tikkie", "... via iDEAL".
_VIA_SUFFIX = re.compile(
    r"\s+via\s+.+?\b(betaalverzoek|tikkie|ideal|payment request)\b.*$",
    re.IGNORECASE)

# Trailing terminal / store code, e.g. "HEMA EV0027", "Huiskamer MP 0172".
# An optional short letter group, then three or more digits, at the very end.
_TERMINAL_CODE = re.compile(r"\s+[A-Za-z]{0,3}\s?\d{3,}\s*$")

# Trailing country code some descriptors carry, e.g. "Foo Bar, NL".
_COUNTRY_SUFFIX = re.compile(r"\s*,\s*[A-Z]{2}\s*$")

# The city (and country) that bunq appends to a card payment description,
# e.g. "Baylings LEEUWARDEN, NL".  We only grab the final word before the
# comma; that is enough to cut it (and any store code behind it) from the name.
_CITY_IN_DESC = re.compile(r"([^\s,]+)\s*,\s*[A-Z]{2}\s*$")


def city_from_description(description):
    """Pull the city out of a bunq card description, or None.

    bunq formats card descriptions as "<merchant> <CITY>, <CC>", so the word
    right before the ", CC" suffix is (the tail of) the city.
    """
    if not description:
        return None
    m = _CITY_IN_DESC.search(description.strip())
    if not m:
        return None
    city = m.group(1)
    return city if len(city) >= 4 else None


def _strip_city(name, city):
    """Cut a known city (and anything after it) from a descriptor."""
    if not city:
        return name
    m = re.search(r"\s+" + re.escape(city) + r"\b", name, re.IGNORECASE)
    if m and m.start() >= 2:
        return name[:m.start()]
    return name


def clean_rules(name, city=None):
    """Rule-based payee clean-up.  Always returns a non-empty string when the
    input is non-empty: if a rule would empty the name we keep the previous
    value instead."""
    if not name:
        return name
    cleaned = name.split(" - ")[0]
    cleaned = _PSP_PREFIX.sub("", cleaned)
    cleaned = _VIA_SUFFIX.sub("", cleaned)
    cleaned = _strip_city(cleaned, city)
    cleaned = _COUNTRY_SUFFIX.sub("", cleaned)
    cleaned = _TERMINAL_CODE.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    # Never return an empty payee; fall back to the bank's name.
    return cleaned or name.split(" - ")[0].strip() or name


def _mode():
    # Read lazily so the pure functions above stay importable without a loaded
    # config (e.g. from the unit tests).
    try:
        from lib.config import config
        return (config.get("payee_cleanup", "rules") or "rules").lower()
    except Exception:
        return "rules"


def clean(display_name, description=None, is_card=False):
    """Public entry point used by the sync.  Honours the "payee_cleanup"
    config setting: "none" (legacy behaviour) or "rules" (default)."""
    if not display_name:
        return display_name

    if _mode() == "none":
        return display_name.split(" - ")[0].strip()

    city = city_from_description(description) if (is_card and description) else None
    return clean_rules(display_name, city=city)
