"""Validation error formatting for structured API error messages.

Parses validation errors into a single, human-readable formatted string with
indentation and struct-field indexing for collections.  Used by all service
client packages when request validation fails.

Mirrors Go ``pkg/edgegriderr`` — ``ParseValidationErrors()`` and helpers.
"""


def parse_validation_errors(errors: dict[str, str | dict | None]) -> str | None:
    """Parse validation errors into easily readable form.

    Formats error(s) into a single formatted string consisting of all
    validation errors that occurred in human-readable form with indentation
    and struct field indexing for collections.

    Mirrors Go ``pkg/edgegriderr.ParseValidationErrors``.

    Args:
        errors: Dictionary mapping field names to error messages (strings),
                nested error dictionaries, or ``None``.  ``None`` values are
                filtered out before formatting.

    Returns:
        Formatted error string, or ``None`` if no errors remain after
        filtering.
    """
    filtered = {k: v for k, v in errors.items() if v is not None}
    if not filtered:
        return None

    result = _parse_errors(filtered, "", 0)
    return result.rstrip("\n")


def _parse_errors(
    validation_errors: dict,
    indexed_field_name: str,
    indent_size: int,
) -> str:
    """Recursively format validation errors with proper indentation.

    Mirrors the inner closure returned by Go's
    ``validationErrorsParser()``.

    Args:
        validation_errors: Dictionary of field-name → error-value mappings.
        indexed_field_name: The parent field name to use when the current
            key is a numeric collection index.
        indent_size: Current indentation depth (number of tab characters).

    Returns:
        Formatted string fragment (may contain trailing newlines).
    """
    keys = sorted(validation_errors.keys())
    parts: list[str] = []

    for key in keys:
        value = validation_errors[key]
        if value is None:
            continue

        # Nested error dictionary — recurse.
        if isinstance(value, dict):
            if _is_numeric(key):
                # Numeric key → collection-index format:
                #   <indexed_field_name>[<key>]: { … }
                inner = _parse_errors(value, "", indent_size + 1)
                parts.append(
                    f"{_indent(indent_size)}{indexed_field_name}[{key}]: "
                    f"{{\n{inner}{_indent(indent_size)}}}\n"
                )
            elif _has_numeric_keys(value):
                # Non-numeric key whose children are all numeric indices →
                # delegate directly without wrapping in braces, passing this
                # key as the new indexed_field_name.
                parts.append(
                    _parse_errors(value, key, indent_size)
                )
            else:
                # Non-numeric key with non-numeric children → wrap in braces.
                inner = _parse_errors(value, key, indent_size + 1)
                parts.append(
                    f"{_indent(indent_size)}{key}: "
                    f"{{\n{inner}{_indent(indent_size)}}}\n"
                )
        else:
            # Leaf error (plain string).
            parts.append(
                f"{_indent(indent_size)}{key}: {value}\n"
            )

    return "".join(parts)


def _indent(size: int) -> str:
    """Return a tab-based indentation string.

    Args:
        size: Number of tab characters.

    Returns:
        A string of *size* tab characters.
    """
    return "\t" * size


def _is_numeric(key: str) -> bool:
    """Check whether *key* represents a numeric collection index.

    Args:
        key: The dictionary key to test.

    Returns:
        ``True`` if *key* can be parsed as an integer, ``False`` otherwise.
    """
    try:
        int(key)
        return True
    except ValueError:
        return False


def _has_numeric_keys(errors: dict) -> bool:
    """Check whether every key in *errors* is a numeric index.

    Args:
        errors: A dictionary of validation errors.

    Returns:
        ``True`` if **all** keys are numeric strings (or the dict is empty),
        ``False`` otherwise.
    """
    return all(_is_numeric(k) for k in errors)
