"""Unit tests for ProphetModelCache TTL expiration and LRU eviction."""

import time

from models.prophet_model import ProphetModelCache


class DummyModel:
    pass


def test_cache_returns_model_before_ttl_expires() -> None:
    cache = ProphetModelCache(ttl_seconds=60, max_size=2)
    model = DummyModel()

    cache.set(1, model)

    assert cache.get(1) is model


def test_cache_expires_model_after_ttl() -> None:
    cache = ProphetModelCache(ttl_seconds=0, max_size=2)
    model = DummyModel()

    cache.set(1, model)
    time.sleep(0.01)

    assert cache.get(1) is None


def test_cache_evicts_least_recently_used_model() -> None:
    cache = ProphetModelCache(ttl_seconds=60, max_size=2)
    first = DummyModel()
    second = DummyModel()
    third = DummyModel()

    cache.set(1, first)
    cache.set(2, second)
    assert cache.get(1) is first  # touch key 1 → key 2 becomes LRU
    cache.set(3, third)           # evicts key 2

    assert cache.get(2) is None
    assert cache.get(1) is first
    assert cache.get(3) is third
