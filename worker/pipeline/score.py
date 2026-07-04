"""Viral-moment detection + Judge Agent.

For a transcript that fits one prompt we make a SINGLE batched Groq call (the
free-tier-friendly design). For long videos we WINDOW the transcript and score
each window, then judge globally — so clips are chosen from across the whole
video instead of only the slice that happened to fit in one prompt. This is the
main fix for "random / no-context" clips on longer videos.

The 'judge' work is the local _select pass: clamp times, enforce length, drop
weak and overlapping picks, and spread them out. Clips are then snapped to real
SENTENCE boundaries (snap_to_sentences) so each one starts and ends on a
complete thought instead of a mid-sentence cut.
"""
import json
import re
