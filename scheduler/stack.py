from typing import Iterable, TypeVar, Iterator, Optional, Sequence, Generic
from attrs import frozen


MAX_VALID_SWAP_DEPTH = 16


T = TypeVar('T')


@frozen
class Stack(Generic[T]):
    values: tuple[T, ...]

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[T]:
        return iter(self.values)

    def __repr__(self) -> str:
        return repr(list(self.values))

    def peek(self) -> Optional[T]:
        if self.values:
            return self.values[-1]
        else:
            return None

    def swap(self, depth: int) -> tuple['Stack', str]:
        assert depth in range(
            1,
            min(len(self.values), MAX_VALID_SWAP_DEPTH + 1)
        ), f'Invalid depth {depth} ({self.values})'
        values = list(self.values)
        values[-1], values[-depth-1] = values[-depth-1], values[-1]
        return Stack(tuple(values)), f'swap{depth}'

    def count(self, node: T, max_count: int = 1024) -> int:
        count = 0

        for value in self.values:
            if value == node:
                count += 1
                if count >= max_count:
                    return max_count

        return count

    def tail(self) -> Sequence[T]:
        return self.values[:-1]

    def push_onto(self, rev_values: Iterable[T]) -> 'Stack':
        new_values = self.values
        for value in rev_values:
            new_values += (value,)
        return Stack(new_values)

    def push(self, value: T) -> 'Stack':
        return Stack(self.values + (value,))

    def get(self, depth: int) -> T:
        assert depth in range(len(self.values))
        return self.values[-depth - 1]

    def pop(self) -> tuple['Stack', T]:
        return Stack(self.values[:-1]), self.values[-1]

    def swap_to_top(self, value: T) -> tuple['Stack[T]', Optional[str]]:
        if self.values[-1] == value:
            return self, None
        i = self.values.index(value)
        depth = len(self.values) - 1 - i
        return self.swap(depth)
