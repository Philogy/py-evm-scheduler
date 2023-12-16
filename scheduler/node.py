from typing import NamedTuple, Generator, Union

Value = Union['Node', str]
Ass = NamedTuple('Ass', [('var', str), ('value', Value)])


class Node(NamedTuple('Node', [
    ('name', str),
    ('operands', tuple[Value, ...])
])):
    @classmethod
    def lit(cls, s: str) -> 'Node':
        return Node(s, tuple())

    def dfs_schedule(self) -> Generator[str, None, None]:
        for op in self.operands:
            yield from op.dfs_schedule()
        yield self.name

    def has_dep(self, other: 'Node') -> bool:
        res = other == self or any(
            operand.has_dep(other)
            for operand in self.operands
        )
        return res

    def __repr__(self) -> str:
        if not self.operands:
            return self.name
        return f'{self.name}({", ".join(map(str, self.operands))})'


def lit(s: str, *args: Node) -> Node:
    return Node(s, args)
