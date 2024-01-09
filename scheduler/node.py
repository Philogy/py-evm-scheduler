from typing import Optional
from functools import cache


class Node:
    name: str
    operands: tuple['EffectfulNode', ...]
    is_constant: bool
    dependencies: set['Node']
    __cached_hash: int

    def __init__(
        self,
        name: str,
        *operands: 'EffectfulNode',
        is_constant: bool = False,
    ) -> None:
        self.name = name
        self.operands = operands
        self.is_constant = is_constant

        self.dependencies = set()
        for operand in operands:
            self.dependencies.add(operand.node)
            self.dependencies.update(operand.dependencies)

        self.__cached_hash = hash((self.name, self.operands, self.is_constant))

    def __hash__(self) -> int:
        return self.__cached_hash

    def has_dependency(self, dependency: 'Node') -> bool:
        return dependency in self.dependencies


class EffectfulNode:
    node: Node
    post_effects: tuple['EffectfulNode', ...] = tuple()
    dependencies: set['Node']
    __cached_hash: int

    def __init__(self, node: Node, post_effects: tuple['EffectfulNode', ...] = tuple()) -> None:
        self.node = node
        self.post_effects = post_effects
        self.dependencies = node.dependencies.copy()
        for effect in post_effects:
            self.dependencies.update(effect.dependencies)
        self.__cached_hash = hash((self.node, self.post_effects))

    def __hash__(self) -> int:
        return self.__cached_hash

    @property
    def name(self) -> str:
        return self.node.name

    @property
    def is_constant(self) -> bool:
        return self.node.is_constant

    @cache
    def has_dependency(self, dependency: 'Node') -> bool:
        return dependency in self.dependencies


def enode(name: str, *operands, post: Optional[list[EffectfulNode]] = None, is_constant=False) -> EffectfulNode:
    if post is None:
        post = []

    return EffectfulNode(
        Node(
            name,
            *operands,
            is_constant=is_constant
        ),
        post_effects=tuple(post)
    )


def const(name: str) -> EffectfulNode:
    return enode(name, is_constant=True)


class DuplicateNodeError(Exception):
    pass


def validate_no_duplicates(nodes: list[Node]) -> set[Node]:
    unique_nodes: set[Node] = set()
    for node in nodes:
        if node in unique_nodes:
            raise DuplicateNodeError(f'Found duplicate node ({node})')
        unique_nodes.add(node)
    return unique_nodes
