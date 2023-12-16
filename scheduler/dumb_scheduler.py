from .node import Node
from collections import defaultdict


def count_nodes(count: dict[Node, int], nodes: tuple[Node, ...]):
    for node in nodes:
        count[node] += 1
        count_nodes(count, node.operands)


def schedule_dumb(
    stack_in: tuple[Node, ...],
    stack_out: tuple[Node, ...],
    effects: tuple[Node, ...]
) -> tuple[str, ...]:
    count: dict[Node, int] = defaultdict(int)
    count_nodes(count, stack_out)
    count_nodes(count, effects)

    stack = stack_in
    schedule
