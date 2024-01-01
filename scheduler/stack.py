from typing import NamedTuple, Optional, TypeVar
from collections import defaultdict
from .node import Node


T = TypeVar('T')


def swap(l: list[T], i: int, swaps: list[int]):
    assert i >= 0
    if i > 0:
        swaps.append(i)
        l[0], l[i] = l[i], l[0]


def get_swaps(stack_in: list[T], stack_out: list[T]) -> list[int]:
    assert len(stack_in) == len(stack_out)
    move: dict[int, T] = {}
    dest: dict[T, list[int]] = defaultdict(list)
    total = 0
    for i, (x, y) in enumerate(zip(stack_in, stack_out)):
        if x != y:
            total += 1
            move[i] = x
            dest[y].append(i)
    swaps: list[int] = []
    for _ in range(total):
        top = stack_in[0]
        if dest[top]:
            to = dest[top].pop()
            swap(stack_in, to, swaps)
            del move[to]
        else:
            frm, val = next(iter(move.items()))
            swap(stack_in, frm, swaps)
            to = dest[val].pop()
            swap(stack_in, to, swaps)
            del move[to]
    return swaps


class Stack(NamedTuple('Stack', [('values', tuple[Node, ...])])):
    def top(self) -> Node:
        return self.values[-1]

    def __len__(self) -> int:
        return len(self.values)

    def __repr__(self) -> str:
        return repr(list(self.values))

    def swap(self, depth: int) -> 'Stack':
        assert depth in range(1, len(self.values))
        values = list(self.values)
        values[-1], values[-depth-1] = values[-depth-1], values[-1]
        return Stack(tuple(values))

    def reorg_to_top(self, target_top: tuple[Node, ...]) -> tuple['Stack', tuple[str, ...]]:
        assert len(target_top) <= len(self.values)
        values = list(self.values)[::-1]
        target = list(target_top)[::-1] + values[len(target_top):]
        swap_indices = get_swaps(values, target)
        swaps = tuple(
            f'swap{si}'
            for si in swap_indices
        )
        return Stack(tuple(target_top)), swaps

    def push(self, value: Node) -> 'Stack':
        return Stack(self.values + (value,))

    def get(self, depth: int) -> Node:
        assert depth in range(len(self.values))
        return self.values[-depth - 1]

    def pop(self) -> tuple[Node, 'Stack']:
        return self.values[-1], Stack(self.values[:-1])

    def swap_to_top(self, value: Node) -> tuple['Stack', Optional[str]]:
        if self.values[-1] == value:
            return self, None
        i = self.values.index(value)
        depth = len(self.values) - 1 - i
        return self.swap(depth), f'swap{depth}'
