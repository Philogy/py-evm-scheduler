from typing import Optional
from attrs import frozen, field


@frozen
class Node:
    name: str
    operands: tuple['Node', ...]
    alias: Optional[str]
    depth: int = field()
    commutative: bool = False

    def __init__(self, name: str, *operands: 'Node', alias: Optional[str] = None, commutative: bool = False) -> None:
        if operands:
            depth = max(op.depth for op in operands) + 1
        else:
            depth = 0
        self.__attrs_init__(
            name,
            operands,
            alias,
            depth,
            commutative
        )

    @classmethod
    def lit(cls, name: str) -> 'Node':
        return Node(name, alias=name)

    MULTILINE_THRESHOLD = 30
    SPACE_PER_INDENT_LEVEL = 2

    def _repr(self, depth: int) -> str:
        if self.alias is not None:
            return f'{self.alias}[{self.depth}]'

        total_op_repr_len = sum(map(
            lambda op: len(op._repr(0)),
            self.operands
        ))

        base_indent = ' ' * self.SPACE_PER_INDENT_LEVEL
        outer_indent = base_indent * depth
        inner_indent = base_indent * (depth + 1)

        header = f'{self.name}[{self.depth}]'
        if total_op_repr_len >= self.MULTILINE_THRESHOLD:
            return f'{header}(\n'\
                + inner_indent + f',\n{inner_indent}'.join(map(lambda op: op._repr(depth + 1), self.operands))\
                + f'\n{outer_indent})'
        else:
            return f'{header}({", ".join(map(str, self.operands))})'

    def __repr__(self) -> str:
        return self._repr(0)

    def has_dependency(self, dependency: 'Node') -> bool:
        return self.depth > dependency.depth and (
            any(
                operand == dependency or
                operand.has_dependency(dependency)
                for operand in self.operands
            )
        )


class DuplicateNodeError(Exception):
    pass


def validate_no_duplicates(nodes: list[Node]) -> set[Node]:
    unique_nodes: set[Node] = set()
    for node in nodes:
        if node in unique_nodes:
            raise DuplicateNodeError(f'Found duplicate node ({node})')
        unique_nodes.add(node)
    return unique_nodes
