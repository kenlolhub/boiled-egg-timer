"""Centralized egg timing logic for the egg timer app."""

from __future__ import annotations

from typing import Dict


# Base cook times in seconds for each doneness target.
DONENESS_BASE_SECONDS: Dict[str, int] = {
    "Jammy": 7 * 60,
    "Soft boiled": int(6.5 * 60),
    "Hard boiled": int(10.5 * 60),
}

# Add a small penalty for each extra egg after the first.
SECONDS_PER_EXTRA_EGG = 4


def calculate_cook_seconds(egg_count: int, doneness: str, custom_seconds: int = 480) -> int:
    """Return total cook time in seconds based on eggs and doneness."""
    if egg_count < 1:
        raise ValueError("egg_count must be at least 1")

    if doneness == "Custom":
        base_seconds = custom_seconds
    elif doneness not in DONENESS_BASE_SECONDS:
        valid = ", ".join(DONENESS_BASE_SECONDS.keys())
        raise ValueError(f"doneness must be one of: {valid}, Custom")
    else:
        base_seconds = DONENESS_BASE_SECONDS[doneness]

    extra_eggs = max(0, egg_count - 1)
    adjustment = extra_eggs * SECONDS_PER_EXTRA_EGG
    return base_seconds + adjustment


def format_mm_ss(total_seconds: int) -> str:
    """Format seconds as MM:SS string."""
    if total_seconds < 0:
        total_seconds = 0
    minutes, seconds = divmod(int(total_seconds), 60)
    return f"{minutes:02d}:{seconds:02d}"
