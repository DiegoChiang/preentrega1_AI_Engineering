"""Reintentos asíncronos con backoff exponencial y jitter."""

import asyncio
import random
from collections.abc import Awaitable, Callable


async def retry_async[T](
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    base_delay: float = 0.25,
    max_delay: float = 4.0,
) -> T:
    """Ejecuta una operación y reintenta fallos transitorios."""

    if attempts < 1:
        raise ValueError("attempts debe ser al menos 1")

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except asyncio.CancelledError:
            raise
        except retry_on:
            if attempt == attempts:
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            await asyncio.sleep(delay + random.uniform(0, delay * 0.15))

    raise RuntimeError("Estado de reintento inalcanzable")

