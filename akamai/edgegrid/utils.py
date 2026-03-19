"""Shared utilities for error content processing.

Provides functions for unescaping HTML content in API error responses.
Mirrors Go pkg/errs (AkamaiOPEN-edgegrid-golang/pkg/errs/error.go).
"""

import html


def _is_html(data: str) -> bool:
    """Check if the given string contains HTML or XML data.

    Mirrors Go pkg/errs.isHTML which uses html.Parse to detect HTML content.
    Go's html.Parse is extremely permissive and succeeds on essentially any
    input string. This implementation checks for the presence of ``&`` or ``<``
    characters which are the only characters that html.unescape would act on,
    providing functionally equivalent behavior.

    Args:
        data: The string to check.

    Returns:
        True if the data appears to contain HTML/XML content.
    """
    return "&" in data or "<" in data


def unescape_content(content: str) -> str:
    """Unescape HTML content from API error responses.

    Checks if the content contains HTML/XML markup and unescapes HTML entities
    if so. Returns the original content unchanged if it is not HTML.

    Mirrors Go pkg/errs.UnescapeContent.

    Args:
        content: The string content to potentially unescape.

    Returns:
        The unescaped content if it was HTML, otherwise the original content.
    """
    if _is_html(content):
        return html.unescape(content)
    return content
