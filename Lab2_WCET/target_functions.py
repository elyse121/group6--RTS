"""
target_functions.py
===================
Three target functions with different control-flow shapes, each paired with
two input-generation strategies:

  * a RANDOM / REPRESENTATIVE strategy  (what "typical" inputs look like)
  * an ADVERSARIAL strategy             (hand-derived to hit the longest path)

Every target takes exactly ONE argument (a tuple when several values are
needed), so the measurement harness can treat all of them identically.

Input generators have the signature  generator(n, rng) -> list of n inputs,
where `rng` is a numpy Generator (seeded in main.py for reproducibility).
"""

import numpy as np

# --------------------------------------------------------------------------
# 1. EARLY-EXIT BRANCH  --  linear search that stops when the key is found
# --------------------------------------------------------------------------
DATA_SIZE = 2000
# A fixed data set shared by all calls (built once, outside any timing).
# Plain Python ints (NOT numpy ints) so every comparison costs the same.
_SEARCH_DATA = [int(x) for x in np.random.default_rng(12345).permutation(DATA_SIZE * 10)[:DATA_SIZE]]


def early_exit_search(key):
    """Scan the data left-to-right and return the index of `key`, or -1.

    Control flow: the loop exits EARLY as soon as the key is found.
    Cost is proportional to the key's position.
    Worst path (hand-derived): key NOT in the data -> all DATA_SIZE
    iterations run and the loop never takes the early exit.
    """
    for i in range(len(_SEARCH_DATA)):
        if _SEARCH_DATA[i] == key:
            return i              # early exit
    return -1                     # fell through the whole loop


def early_exit_random(n, rng):
    """Representative: the key is present, at a uniformly random position."""
    positions = rng.integers(0, DATA_SIZE, size=n)
    return [_SEARCH_DATA[p] for p in positions]


def early_exit_adversarial(n, rng):
    """Adversarial: a key that is absent (-1 never occurs in the data), so
    the scan has to visit every element.  A few different absent keys are
    used so the measurement is not one repeated constant value."""
    return [int(-1 - k) for k in rng.integers(0, 50, size=n)]


# --------------------------------------------------------------------------
# 2. DATA-DEPENDENT LOOP  --  Collatz iteration count depends on the value
# --------------------------------------------------------------------------
COLLATZ_MAX_INPUT = 100_000


def collatz_steps(n):
    """Count steps of the Collatz sequence until n reaches 1.

    Control flow: a while-loop whose trip count depends on the DATA, not on
    the input size.  Nearby inputs can have very different step counts.
    """
    steps = 0
    while n != 1:
        if n % 2 == 0:
            n //= 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps


def _longest_collatz_input(limit):
    """Hand-derivation helper: brute-force the input in [1, limit] with the
    most steps (done ONCE, at import, outside any timed region).  This is
    the 'static-analysis-like' step: we reason over the whole input domain
    instead of sampling it.  (Result for limit=100000 is n=77031, 350 steps.)"""
    best_n, best_steps = 1, 0
    for n in range(1, limit + 1):
        s = collatz_steps(n)
        if s > best_steps:
            best_n, best_steps = n, s
    return best_n


_COLLATZ_WORST = _longest_collatz_input(COLLATZ_MAX_INPUT)


def collatz_random(n, rng):
    """Representative: inputs uniformly distributed over the legal domain."""
    return [int(x) for x in rng.integers(2, COLLATZ_MAX_INPUT + 1, size=n)]


def collatz_adversarial(n, rng):
    """Adversarial: always the worst input of the whole domain (n=77031,
    350 steps), found by exhaustive search above."""
    return [_COLLATZ_WORST] * n


# --------------------------------------------------------------------------
# 3. NESTED CONDITIONALS  --  packet handler with a deep, expensive path
# --------------------------------------------------------------------------
def _checksum(iterations):
    """Small busy computation whose cost is proportional to `iterations`."""
    acc = 0
    for i in range(iterations):
        acc = (acc * 31 + i) & 0xFFFF
    return acc


def classify_packet(packet):
    """Handle a packet (size, priority, flags, checksum_ok).

    Control flow: three levels of nested conditionals.  Each path does a
    different amount of work:

        size <= 0                                        -> reject   (cheap)
        priority > 5 and flags&1 and NOT checksum_ok     -> 300 iters (WORST)
        priority > 5 and flags&1 and checksum_ok         ->  40 iters
        priority > 5 and not flags&1                     ->  80 iters
        priority <= 5 and size > 1000 and flags&2        -> 150 iters
        priority <= 5 and size > 1000 and not flags&2    ->  50 iters
        priority <= 5 and size <= 1000                   ->  10 iters
    """
    size, priority, flags, checksum_ok = packet
    if size <= 0:
        return 0                                   # early reject
    if priority > 5:                               # high-priority branch
        if flags & 1:                              # "needs verification"
            if checksum_ok:
                return _checksum(40)
            else:
                return _checksum(300)              # error recovery: WORST PATH
        return _checksum(80)
    else:                                          # normal-priority branch
        if size > 1000:
            if flags & 2:
                return _checksum(150)
            return _checksum(50)
        return _checksum(10)


def packet_random(n, rng):
    """Representative traffic: random sizes/priorities/flags, 90% of
    checksums valid.  The worst path is reachable but RARE (~2% of calls)."""
    sizes = rng.integers(0, 1501, size=n)
    prios = rng.integers(0, 10, size=n)
    flags = rng.integers(0, 4, size=n)
    ok = rng.random(n) < 0.9
    return [(int(s), int(p), int(f), bool(o)) for s, p, f, o in zip(sizes, prios, flags, ok)]


def packet_adversarial(n, rng):
    """Adversarial: always take priority>5, flags&1 set, checksum invalid
    (the 300-iteration recovery path).  Size and priority vary a little
    within the legal region that still reaches that path."""
    sizes = rng.integers(1, 1501, size=n)
    prios = rng.integers(6, 10, size=n)
    return [(int(s), int(p), 1, False) for s, p in zip(sizes, prios)]


# Registry used by main.py: (display name, function, random gen, adversarial gen, one-line description)
TARGETS = [
    ("early_exit_search", early_exit_search, early_exit_random, early_exit_adversarial,
     "Linear search with early exit; worst case = key absent"),
    ("collatz_loop", collatz_steps, collatz_random, collatz_adversarial,
     "Data-dependent while-loop; worst case = input with most steps"),
    ("nested_packet", classify_packet, packet_random, packet_adversarial,
     "Nested conditionals; worst case = deepest error-recovery path"),
]
