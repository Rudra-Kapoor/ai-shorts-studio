"""Build an ASS subtitle file for a clip, in one of several viral styles.

Styles (Phase 2):
  - hormozi : big bold WHITE, thick black outline, UPPERCASE, 1-3 words
  - mrbeast : huge bold YELLOW, extra-thick outline, UPPERCASE, 1-2 words
  - minimal : smaller clean white, thin outline, normal case, fuller lines
  - clean   : medium white, soft outline, sentence-case, 3-4 words

Times are made relative to the clip start so they line up with the trimmed
video. Uses the Liberation font installed in the Docker image so libass can
actually render the text.
"""
import config

# Per-style configuration. Colours are ASS &HAABBGGRR.
STYLES = {
    "hormozi": dict(size=120, primary="&H00FFFFFF", outline_col="&H00101010",
                    bold=-1, outline=7, shadow=3, marginv=360,
                    uppercase=True, max_words=3, max_chars=16, fade=(60, 0)),
    "mrbeast": dict(size=132, primary="&H0000FFFF", outline_col="&H00000000",
                    bold=-1, outline=8, shadow=4, marginv=380,
                    uppercase=True, max_words=2, max_chars=12, fade=(40, 0)),
    "minimal": dict(size=66, primary="&H00FFFFFF", outline_col="&H00000000",
                    bold=0, outline=2, shadow=0, marginv=240,
                    uppercase=False, max_words=6, max_chars=30, fade=(80, 0)),
    "clean":   dict(size=84, primary="&H00FFFFFF", outline_col="&H00141414",
                    bold=-1, outline=4, shadow=2, marginv=300,
                    uppercase=False, max_words=4, max_chars=20, fade=(60, 0)),
}
