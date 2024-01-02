from typing import Iterable, Iterator, Optional, Sequence
from attrs import frozen
from .node import Node


MAX_VALID_SWAP_DEPTH = 16


@frozen
class Stack:
    values: tuple[Node, ...]

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self) -> Iterator[Node]:
        return iter(self.values)

    def __repr__(self) -> str:
        return repr(list(self.values))

    def peek(self) -> Node:
        return self.values[-1]

    def swap(self, depth: int) -> tuple['Stack', str]:
        assert depth in range(
            1,
            min(len(self.values), MAX_VALID_SWAP_DEPTH + 1)
        ), f'Invalid depth {depth} ({self.values})'
        values = list(self.values)
        values[-1], values[-depth-1] = values[-depth-1], values[-1]
        return Stack(tuple(values)), f'swap{depth}'

    def count(self, node: Node) -> int:
        return sum(
            value == node
            for value in self.values
        )

    def push_operands_onto(self, node: Node) -> 'Stack':
        '''
            call_params: gas, addr, val, cd_start, cd_len, ret_start, ret_len
        '''
        new_values = self.values
        for value in reversed(node.operands):
            new_values += (value,)
        return Stack(new_values)

    def push(self, value: Node) -> 'Stack':
        return Stack(self.values + (value,))

    def get(self, depth: int) -> Node:
        assert depth in range(len(self.values))
        return self.values[-depth - 1]

    def pop(self) -> tuple['Stack', Node]:
        return Stack(self.values[:-1]), self.values[-1]

    def swap_to_top(self, value: Node) -> tuple['Stack', Optional[str]]:
        if self.values[-1] == value:
            return self, None
        i = self.values.index(value)
        depth = len(self.values) - 1 - i
        return self.swap(depth)
