import re


def redact_secret(value: object, secret: str | None) -> str:
    """Return text safe for logs and API errors, redacting full or partial secrets."""
    text = str(value)
    if not secret:
        return text

    # Redact the full credential and any embedded fragment of at least 8 chars.
    # Longest-first matching avoids leaving the tail of an overlapping fragment.
    fragments = {secret}
    fragments.update(secret[start : start + length]
                     for length in range(8, len(secret) + 1)
                     for start in range(len(secret) - length + 1))
    pattern = re.compile("|".join(re.escape(part) for part in sorted(fragments, key=len, reverse=True)))
    return pattern.sub("[REDACTED]", text)
