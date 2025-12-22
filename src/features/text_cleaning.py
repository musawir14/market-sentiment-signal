import re

_whitespace = re.compile(r"\s+")
_url = re.compile(r"https?://\S+|www\.\S+")
_non_text = re.compile(r"[^A-Za-z0-9\s\.\,\!\?\%\$\-\']+")


def clean_text(s: str) -> str:
    """
    Light cleaning for titles/headlines:
    - remove URLs
    - remove weird characters
    - normalize whitespace
    """
    if not isinstance(s, str):
        return ""
    s = s.strip()
    s = _url.sub("", s)
    s = _non_text.sub(" ", s)
    s = _whitespace.sub(" ", s)
    return s.strip()
