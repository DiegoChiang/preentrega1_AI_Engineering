import asyncio

import pytest

from incident_intelligence.retry import retry_async


@pytest.mark.asyncio
async def test_retry_returns_after_transient_failures() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("temporal")
        return "ok"

    result = await retry_async(operation, attempts=3, base_delay=0, max_delay=0)

    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_propagates_cancellation() -> None:
    async def operation() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await retry_async(operation, attempts=3, base_delay=0, max_delay=0)
