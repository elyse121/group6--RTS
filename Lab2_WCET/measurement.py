"""
measurement.py
==============
A small, reusable measurement harness (Section 1.7: measurement-based WCET).

It makes NO assumption about the target function's internals: it only calls
`func(input)` and times each call with time.perf_counter().
"""

import gc
import time
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Measurement:
    """Raw result of one measurement campaign (nothing is aggregated here)."""
    name: str                 # target function name
    strategy: str             # e.g. "random" or "adversarial"
    durations: np.ndarray     # one execution time per call, in SECONDS
    inputs: list = field(default_factory=list)  # input used for each call


def measure(func, inputs, repeats=500, warmup=20, name=None, strategy="",
            disable_gc=True):
    """Time `func` on `repeats` inputs and keep EVERY sample.

    Parameters
    ----------
    func     : callable taking exactly one argument.
    inputs   : either a list/sequence of inputs (cycled if shorter than
               `repeats`) or a callable `gen(n)` that returns a list of n inputs.
    repeats  : number of timed calls (hundreds).
    warmup   : untimed calls first, to warm caches / the interpreter.
    disable_gc : pause Python's garbage collector while timing so a GC pass
               is not mistaken for the function's own cost.
    """
    inputs = inputs(repeats) if callable(inputs) else list(inputs)
    if not inputs:
        raise ValueError("inputs must not be empty")
    # Cycle the input list if it is shorter than the repeat count.
    inputs = [inputs[i % len(inputs)] for i in range(repeats)]

    for x in inputs[:warmup]:          # warm-up: results discarded
        func(x)

    durations = np.empty(repeats, dtype=np.float64)
    perf = time.perf_counter           # local alias = less lookup overhead
    gc_was_enabled = gc.isenabled()
    if disable_gc:
        gc.disable()
    try:
        for i, x in enumerate(inputs):
            t0 = perf()
            func(x)
            t1 = perf()
            durations[i] = t1 - t0     # store every single execution time
    finally:
        if disable_gc and gc_was_enabled:
            gc.enable()

    return Measurement(name or getattr(func, "__name__", "func"),
                       strategy, durations, inputs)


def timer_overhead(samples=2000):
    """Estimate the cost of one empty perf_counter() start/stop pair (s).
    This is a floor on what the harness can resolve; it is NOT subtracted
    from measurements (subtracting would make results less conservative)."""
    perf = time.perf_counter
    d = np.empty(samples)
    for i in range(samples):
        t0 = perf()
        t1 = perf()
        d[i] = t1 - t0
    return float(np.median(d))
