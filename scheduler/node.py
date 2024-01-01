from collections import defaultdict
from typing import NamedTuple, Optional


class Node(NamedTuple('Node', [
    ('name', str),
    ('operands', tuple['Node', ...])
])):
    @classmethod
    def lit(cls, s: str) -> 'Node':
        return Node(s, tuple())

    def __repr__(self) -> str:
        if not self.operands:
            return self.name
        return f'{self.name}({", ".join(map(str, self.operands))})'


def has_dep(value: Node, dep: Node) -> bool:
    return value == dep or any(
        has_dep(operand, dep)
        for operand in value.operands
    )


def lit(s: str, *args: Node) -> Node:
    return Node(s, args)


Effect = NamedTuple(
    'Effect',
    [
        ('node', Node),
        ('post', tuple['Effect', ...])
    ]
)

Step = NamedTuple(
    'Step',
    [
        ('var_assign', Optional[str]),
        ('value', Node),
        ('post', tuple[int, ...])
    ]
)


class Block(NamedTuple(
    'Block',
    [
        ('stack_in', tuple[str, ...]),
        ('steps', tuple[Step, ...]),
        ('stack_out', tuple[str, ...])
    ]
)):
    def get_dependent_count(self) -> dict[int, int]:
        dependents = defaultdict(int)
        for step in self.steps:
            for pre_id in step.post:
                dependents[pre_id] += 1
        return dependents
