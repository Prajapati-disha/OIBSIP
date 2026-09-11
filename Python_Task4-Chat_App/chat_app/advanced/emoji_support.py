"""
emoji_support.py — turns shortcodes like :smile: into real Unicode emoji
==========================================================================
Tries to use the popular `emoji` PyPI package first (it knows hundreds
of shortcodes). If that package isn't installed, we fall back to a
small built-in dictionary covering the most common ones, so the
feature still works with zero extra dependencies.
"""

import re

try:
    import emoji as _emoji_lib
    _HAS_EMOJI_LIB = True
except ImportError:
    _HAS_EMOJI_LIB = False

# Fallback dictionary — used either when the `emoji` package is not
# installed, or to guarantee our own curated set always works even if
# the library's naming differs slightly.
FALLBACK_SHORTCODES = {
    ":smile:": "😄",
    ":smiley:": "😃",
    ":grin:": "😁",
    ":laughing:": "😆",
    ":joy:": "😂",
    ":wink:": "😉",
    ":blush:": "😊",
    ":heart:": "❤️",
    ":heart_eyes:": "😍",
    ":thumbsup:": "👍",
    ":thumbsdown:": "👎",
    ":+1:": "👍",
    ":-1:": "👎",
    ":clap:": "👏",
    ":fire:": "🔥",
    ":thinking:": "🤔",
    ":cry:": "😢",
    ":sob:": "😭",
    ":angry:": "😠",
    ":wave:": "👋",
    ":tada:": "🎉",
    ":100:": "💯",
    ":eyes:": "👀",
    ":pray:": "🙏",
    ":sunglasses:": "😎",
    ":sweat_smile:": "😅",
    ":rofl:": "🤣",
    ":ok_hand:": "👌",
    ":raised_hands:": "🙌",
    ":partying_face:": "🥳",
    ":skull:": "💀",
}

_SHORTCODE_PATTERN = re.compile(r":[a-zA-Z0-9_+\-]+:")


def render_emoji(text: str) -> str:
    """Convert every recognized :shortcode: in `text` into a Unicode emoji."""
    if _HAS_EMOJI_LIB:
        # language='alias' understands GitHub/Slack-style shortcodes like :smile:
        try:
            text = _emoji_lib.emojize(text, language="alias")
        except TypeError:
            # Older versions of the library don't accept `language=`.
            text = _emoji_lib.emojize(text, use_aliases=True)

    # Always run the fallback map afterward too, in case the library
    # missed a code we care about, or isn't installed at all.
    def _replace(match: "re.Match") -> str:
        code = match.group(0)
        return FALLBACK_SHORTCODES.get(code, code)

    return _SHORTCODE_PATTERN.sub(_replace, text)
