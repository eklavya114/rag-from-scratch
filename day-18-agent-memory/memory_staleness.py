"""
memory_staleness.py

A remembered fact is only useful while it's still true. A preferred
contact method saved a year ago might not be current anymore. This
file shows storing a fact alongside a timestamp, flagging facts older
than a threshold as possibly stale, having the agent confirm a stale
fact before relying on it, and updating the timestamp once confirmed.
"""

STALENESS_THRESHOLD_TICKS = 30  # a simple tick counter stands in for real elapsed time, so this demo is reproducible


class TimestampedFact:
    """A fact paired with the tick it was last confirmed true, not just when it was first saved."""

    def __init__(self, value, saved_at_tick):
        self.value = value
        self.last_confirmed_tick = saved_at_tick

    def is_stale(self, current_tick, threshold=STALENESS_THRESHOLD_TICKS):
        """MARK FACTS OLDER THAN A THRESHOLD AS POSSIBLY STALE: a fact isn't wrong just because time passed, but it's worth double-checking rather than trusting blindly forever."""
        return (current_tick - self.last_confirmed_tick) > threshold

    def confirm(self, current_tick):
        """CONFIRMING A FACT UPDATES ITS TIMESTAMP: once the user re-confirms a fact is still true, it's fresh again from this point forward, without needing to be re-saved as if it were new information."""
        self.last_confirmed_tick = current_tick


def get_fact_for_use(fact, current_tick, confirm_fn):
    """
    ASK THE AGENT TO CONFIRM STALE FACTS BEFORE USING THEM: if the fact
    looks stale, run it past a confirmation step (here, a function
    standing in for asking the user) before trusting it for the current
    task. A confirmed fact gets its timestamp refreshed; a rejected one
    is not used.
    """
    if not fact.is_stale(current_tick):
        return fact.value, "fresh"

    still_true = confirm_fn(fact.value)
    if still_true:
        fact.confirm(current_tick)
        return fact.value, "confirmed_after_staleness_check"
    return None, "rejected_as_outdated"


def main():
    print("=== Memory Staleness ===\n")

    print("--- A fact saved a long time ago ---")
    contact_method = TimestampedFact(value="email", saved_at_tick=0)
    print(f"Saved 'email' at tick 0. Staleness threshold: {STALENESS_THRESHOLD_TICKS} ticks.\n")

    current_tick = 10
    print(f"At tick {current_tick}: is_stale = {contact_method.is_stale(current_tick)}")

    current_tick = 45
    print(f"At tick {current_tick}: is_stale = {contact_method.is_stale(current_tick)}\n")

    print("--- Confirming a stale fact (user says it's still true) ---")

    def user_confirms_yes(value):
        print(f"  (asking the user) Is '{value}' still your preferred contact method? -> yes")
        return True

    value, status = get_fact_for_use(contact_method, current_tick=45, confirm_fn=user_confirms_yes)
    print(f"Result: value={value!r}, status={status}")
    print(f"Timestamp refreshed to tick {contact_method.last_confirmed_tick}\n")

    print("--- Checking staleness again, right after confirming ---")
    print(f"At tick 46: is_stale = {contact_method.is_stale(46)} (fresh again, since it was just confirmed)\n")

    print("--- Confirming a stale fact that's actually changed (user says no) ---")
    old_fact = TimestampedFact(value="phone", saved_at_tick=0)

    def user_confirms_no(value):
        print(f"  (asking the user) Is '{value}' still your preferred contact method? -> no, that changed")
        return False

    value, status = get_fact_for_use(old_fact, current_tick=50, confirm_fn=user_confirms_no)
    print(f"Result: value={value!r}, status={status}")

    print(
        "\nWhy freshness matters: trusting an old fact forever risks acting "
        "on something that quietly stopped being true, but re-confirming "
        "every fact on every single use defeats the purpose of remembering "
        "anything at all. A staleness threshold is the middle ground: trust "
        "a recently confirmed fact without asking again, but double-check "
        "anything old enough that it might have changed since the last time "
        "anyone looked at it."
    )


if __name__ == "__main__":
    main()
