from .node import Block, Value
from .stack import Stack
from collections import defaultdict


def schedule_dumb(block: Block) -> tuple[str, ...]:
    dependent_count = block.get_dependent_count()
    last_steps: set[int] = {
        sid
        for sid in range(len(block.steps))
        if dependent_count[sid] == 0
    }
    rem_instances = defaultdict(int)
    schedule: tuple[str, ...] = tuple()

    stack: Stack = Stack(block.stack_out)

    while True:

        break

    return schedule
