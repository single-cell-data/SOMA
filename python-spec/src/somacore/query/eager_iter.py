from concurrent import futures
from typing import Iterator, Optional, TypeVar

_T = TypeVar("_T")


class _EagerIterator(Iterator[_T]):
    def __init__(
        self,
        iterator: Iterator[_T],
        pool: Optional[futures.Executor] = None,
    ):
        super().__init__()
        self.iterator = iterator
        self._pool = pool or futures.ThreadPoolExecutor()
        self._own_pool = pool is None
        self._future: futures.Future[_T] = self._pool.submit(next, self.iterator)  # type: ignore

    def __next__(self) -> _T:
        try:
            res: _T = self._future.result()
            self._future = self._pool.submit(next, self.iterator)  # type: ignore
            return res
        except StopIteration:
            self._cleanup()
            raise

    def _cleanup(self) -> None:
        if self._own_pool:
            self._pool.shutdown()

    def __del__(self) -> None:
        super_del = getattr(super(), "__del__", lambda: None)
        super_del()

        # admit the condition where the iterator was abandoned without
        # completely exhausting the iterator
        self._cleanup()
