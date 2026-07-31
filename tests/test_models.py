"""Tests for OHM core data models."""

import warnings

from ohm.core.models import ProviderInfo


def test_provider_info_still_importable() -> None:
    """ProviderInfo remains importable for backward compatibility."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        info = ProviderInfo(name="anthropic", display_name="Anthropic", status="healthy")
    assert info.name == "anthropic"
    assert info.display_name == "Anthropic"
    assert any(
        issubclass(w.category, DeprecationWarning) for w in caught
    ), "ProviderInfo should emit a DeprecationWarning on use"
