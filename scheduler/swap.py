from collections import defaultdict
from typing import Generator, TypeVar


T = TypeVar('T')


def swap(l: list[T], i: int) -> Generator[int, None, None]:
    assert i >= 0
    if i > 0:
        l[0], l[i] = l[i], l[0]
        yield i


def get_swaps(stack_in: list[T], stack_out: list[T]) -> Generator[int, None, None]:
    assert len(stack_in) == len(stack_out)
    move: dict[int, T] = {}
    dest: dict[T, list[int]] = defaultdict(list)
    total = 0
    for i, (x, y) in enumerate(zip(stack_in, stack_out)):
        if x != y:
            total += 1
            move[i] = x
            dest[y].append(i)
    for _ in range(total):
        top = stack_in[0]
        if dest[top]:
            to = dest[top].pop()
            yield from swap(stack_in, to)
            del move[to]
        else:
            frm, val = next(iter(move.items()))
            yield from swap(stack_in, frm)
            to = dest[val].pop()
            yield from swap(stack_in, to)
            del move[to]
