from collections import defaultdict
from typing import Counter, Generator, Optional
from attrs import frozen, define
from .node import EffectfulNode, Node
from .stack import Stack
from .swap import get_swaps


MAX_DUP = 16


SearchPath = tuple['SearchState', int, list[str]]


@frozen
class SearchState:
    stack: Stack[EffectfulNode]
    effects_to_undo: tuple[EffectfulNode, ...]

    # def __init__(
    #     self,
    #     stack: Stack[EffectfulNode],
    #     effects_to_undo: tuple[EffectfulNode, ...]
    # ) -> None:
    #     self.stack = stack
    #     self.effects_to_undo = effects_to_undo

    # def __hash__(self) -> int:
    #     return hash((self.stack, self.effects_to_undo))

    def has_dependency(self, node: Node) -> bool:
        return not node.is_constant and any(
            value.has_dependency(node)
            for value in self.stack
        ) or any(
            effect.has_dependency(node)
            for effect in self.effects_to_undo
        )

    def undo_effect(self, effect: EffectfulNode) -> SearchPath:
        assert effect in self.effects_to_undo
        i = self.effects_to_undo.index(effect)
        new_effects = self.effects_to_undo[:i] + self.effects_to_undo[i+1:]

        ops: list[str] = []
        new_state = self._undo_node(
            self.stack,
            new_effects,
            ops,
            effect
        )
        return new_state, 0, ops

    def undo_node(self, enode: EffectfulNode) -> SearchPath:
        stack, swap_op = self.stack.swap_to_top(enode)
        ops = []
        weight = 0
        if swap_op is not None:
            ops.append(swap_op)
            weight += 1
        stack, value = stack.pop()
        assert value == enode
        new_state = self._undo_node(stack, self.effects_to_undo, ops, enode)
        return new_state, weight, ops

    def dedup(self, enode: EffectfulNode, depth: int) -> SearchPath:
        # log.debug(f'Deduping {enode} ({depth}) from {self.stack.values}')
        stack = self.stack
        if depth != 0:
            stack, op = stack.swap(depth)
            ops = [op]
            weight = 1
        else:
            ops = []
            weight = 0
        # TODO: Dedup based on first index within 16 range
        dedup_index = stack.values.index(enode)
        assert dedup_index != len(self.stack) - 1
        stack, popped_value = stack.pop()
        assert popped_value == enode
        dup_depth = len(stack) - dedup_index
        assert dup_depth in range(1, MAX_DUP + 1)
        ops.append(f'dup{dup_depth}')

        new_state = SearchState(stack, self.effects_to_undo)

        return new_state, weight, ops

    @classmethod
    def _undo_node(
        cls,
        stack: Stack[EffectfulNode],
        effects_to_undo: tuple[EffectfulNode, ...],
        ops: list[str],
        enode: EffectfulNode
    ) -> 'SearchState':
        stack = stack.push_onto(enode.node.operands[::-1])
        for effect in enode.post_effects:
            effects_to_undo += (effect,)
        ops.append(enode.name)
        return SearchState(stack, effects_to_undo)


@define
class Explored:
    state: SearchState
    prev_state: SearchState
    is_end: bool
    weight: int
    ops_to_prev: list[str]
    index_in_queue: int


def count_nodes(counts: Counter[EffectfulNode], enode: EffectfulNode):
    counts[enode] += 1
    for sub_node in enode.node.operands:
        count_nodes(counts, sub_node)
    for effect in enode.post_effects:
        count_nodes(counts, effect)


class DijkstraSchedule:
    target_input_symbols: list[str]
    input_value_counts: Counter[str]
    input_value_counts_frozen: frozenset[tuple[str, int]]

    explored: dict[SearchState, Explored]
    weight_to_explored: dict[int, list[Explored]]
    best_weight: int
    solution: Optional[list[str]]

    def __init__(
        self,
        target_input_symbols: list[str],
        start_output_stack: list[EffectfulNode],
        start_done_effects: list[EffectfulNode],
    ) -> None:
        self.explored = {}
        self.weight_to_explored = defaultdict(list)
        self.best_weight = 0

        self.target_input_symbols = target_input_symbols
        self.input_value_counts = Counter(target_input_symbols)
        self.input_value_counts_frozen = frozenset(
            self.input_value_counts.items()
        )

        start_state = SearchState(
            Stack(tuple(start_output_stack)),
            tuple(start_done_effects),
        )
        first_explored = Explored(
            start_state,
            start_state,
            False,
            0,
            ops_to_prev=[],
            index_in_queue=0
        )
        self.insert_new(first_explored)

        self.search()

    def search(self):
        while not (top := self.pop_best()).is_end:
            prev_state = top.state
            for next_path in self.next_states(prev_state):
                if next_path is None:
                    continue
                next_state, delta_weight, ops = next_path
                explored_next = self.explored.get(next_state)
                is_end, added_weight = self.complete_for_end(next_state, ops)
                weight = top.weight + delta_weight + added_weight
                if explored_next is None:
                    self.insert_new(Explored(
                        next_state,
                        prev_state,
                        is_end,
                        weight,
                        ops,
                        0
                    ))
                elif weight < explored_next.weight:
                    assert explored_next.is_end == is_end
                    explored_next.prev_state = prev_state
                    explored_next.ops_to_prev = ops
                    self.update_explored(explored_next, weight)
                else:
                    # log.debug(
                    #     f'Discarded worse path to {next_state} (from: {prev_state}, ops: {ops})'
                    # )
                    pass
            self._search_next_best_weight()

        self.put_together_solution(top)

    def put_together_solution(self, top: Explored):
        self.solution = []
        self.solution.extend(top.ops_to_prev[::-1])
        explored = top
        while (prev := self.explored[explored.prev_state]) != explored:
            self.solution.extend(prev.ops_to_prev[::-1])
            explored = prev

    def next_states(self, state: SearchState) -> Generator[Optional[SearchPath], None, None]:
        # log.debug(f'Getting next states from: {state}')

        # Undo dup top of stack
        if (top := state.stack.peek()) is not None:
            yield self.undo_dup(state, top, 0)
            yield self.undo_node(state, top)

        # Undo Effect
        for effect in state.effects_to_undo:
            # log.debug(f'undoing effect {effect}')
            yield state.undo_effect(effect)

        # Undo Node
        for value in state.stack.tail():
            yield self.undo_node(state, value)

        # Undo Dup
        for depth, node in enumerate(reversed(state.stack.tail()), start=1):
            if (next_state := self.undo_dup(state, node, depth)) is not None:
                yield next_state

        # log.debug(f'End of next states')
        # TODO
        yield state, 3, []

    def undo_node(self, state: SearchState, enode: EffectfulNode) -> Optional[SearchPath]:
        if self.is_input_symbol(enode):
            return None
        if self.still_many_on_stack(state, enode):
            return None
        if state.has_dependency(enode.node):
            return None
        # log.debug(f'undoing node {enode}')
        return state.undo_node(enode)

    def still_many_on_stack(self, state: SearchState, enode: EffectfulNode) -> bool:
        return not enode.is_constant and state.stack.count(enode, max_count=2) > 1

    def is_input_symbol(self, enode: EffectfulNode) -> bool:
        return enode.name in self.target_input_symbols

    def undo_dup(self, state: SearchState, enode: EffectfulNode, depth: int) -> Optional[SearchPath]:
        if enode.is_constant:
            return None
        count = state.stack.count(enode)
        if count == 1:
            return None
        if self.input_value_counts[enode.name] >= count:
            return None
        if state.has_dependency(enode.node):
            return None
        # log.debug(f'deduping {enode} at depth {depth}')
        return state.dedup(enode, depth)

    def complete_for_end(self, state: SearchState, ops: list[str]) -> tuple[bool, int]:
        if not self.is_end(state):
            return False, 0

        weight = 0
        names = [value.name for value in state.stack]
        for swap_index in get_swaps(self.target_input_symbols[::-1], names[::-1]):
            ops.append(f'swap{swap_index}')
            weight += 1

        return True, weight

    def is_end(self, state: SearchState) -> bool:
        if state.effects_to_undo or len(state.stack) != len(self.target_input_symbols):
            return False

        state_value_counts: Counter[str] = Counter(map(
            lambda enode: enode.name,
            state.stack
        ))

        return frozenset(state_value_counts.items()) == self.input_value_counts_frozen

    #########################
    #### PRIORITY QUEUE #####
    #########################

    def pop_best(self) -> Explored:
        return self.weight_to_explored[self.best_weight].pop()

    def insert_new(self, explored: Explored):
        self.explored[explored.state] = explored
        self._add_to_weight_map(explored)

    def update_explored(self, explored: Explored, new_weight: int):
        with_weight = self.weight_to_explored[explored.weight]
        last_index = len(with_weight) - 1
        index = explored.index_in_queue
        if index < last_index:
            with_weight[last_index], with_weight[index] = with_weight[index], with_weight[last_index]
            with_weight[index].index_in_queue = index
        with_weight.pop()
        explored.weight = new_weight
        self._add_to_weight_map(explored)

    def _add_to_weight_map(self, explored: Explored):
        with_weight = self.weight_to_explored[explored.weight]
        explored.index_in_queue = len(with_weight)
        with_weight.append(explored)
        self.best_weight = min(self.best_weight, explored.weight)

    def _search_next_best_weight(self):
        while not self.weight_to_explored[self.best_weight]:
            self.best_weight += 1
