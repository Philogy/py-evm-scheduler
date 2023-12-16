from typing import NamedTuple, Sequence, Set
from collections import defaultdict
from .node import Node


Nodes = dict[Node, int]

TreeGraph = NamedTuple(
    'TreeGraph',
    [
        ('trees', Set[int]),
        ('edges', Set[tuple[int, int]])
    ]
)


class Graph(NamedTuple(
    'Graph',
    [
        ('nodes', Nodes),
        ('edges', set[tuple[int, int]])
    ]
)):
    @classmethod
    def from_nodes(cls, nodes: Sequence[Node]) -> 'Graph':
        g = cls({}, set())
        next_id = 0
        for node in nodes:
            next_id = g.add_node(node, next_id)
        return g

    def add_node(self, node: Node, next_id: int) -> int:
        if node not in self.nodes:
            self.nodes[node] = next_id
            next_id += 1
            for suc in node.operands:
                next_id = self.add_node(suc, next_id)
                self.edges.add((self.nodes[node], self.nodes[suc]))
        return next_id

    def is_tree(self) -> bool:
        has_predecessor: set[int] = set()
        for _, suc in self.edges:
            if suc in has_predecessor:
                return False
            has_predecessor.add(suc)
        return True

    def schedule(self) -> list[str]:
        if self.is_tree() and len(roots := self.get_roots()) == 1:
            return list(roots[0].dfs_schedule())

        predecessors: dict[int, int] = defaultdict(int)
        for _, suc in self.edges:
            predecessors[suc] += 1

        cut_set = {
            (pre, suc)
            for pre, suc in self.edges
            if predecessors[suc] > 1
        }

        forest = Graph(self.nodes, self.edges - cut_set)

        roots = forest.get_roots()

        tg = TreeGraph(
            {
                self.nodes[root]
                for root in roots
            },
            {
                (u, v)
                for u, v in self.edges
                if u in roots and v in roots
            }
        )

        print(f'tg: {tg}')

        print(f'roots: {roots}')

        assert False

    def get_roots(self) -> list[Node]:
        return [
            node
            for node in self.nodes
            if not any(
                v == self.nodes[node]
                for _, v in self.edges
            )
        ]
