from collections import Counter
from typing import Generator, Optional, Sequence
from attrs import define, frozen
from .node import Node
from .stack import Stack
from .logging import log
from .swap import get_swaps


@define
class Solution:
    weight: int
    steps: list[str]


@define
class Action:
    pass


Trace = tuple[str, ...]

MAX_DUP = 16
EFFECT_WRAPPER_NODE = '__effect__'


@frozen
class SearchState:
    stack: Stack
    effects_to_undo: frozenset[Node]
    trace: Trace = tuple()
    weight: int = 0

    def undo_effect(self, effect: Node) -> 'SearchState':
        new_effects = set(self.effects_to_undo)

        assert effect in new_effects
        new_effects.remove(effect)

        return self._undo_node(
            self.stack,
            new_effects,
            self.trace,
            self.weight,
            effect
        )

    def has_dependency(self, node: Node) -> bool:
        return any(
            value.has_dependency(node)
            for value in self.stack
        ) or any(
            effect.has_dependency(node)
            for effect in self.effects_to_undo
        )

    def undo_node(self, node: Node) -> 'SearchState':
        stack, swap_op = self.stack.swap_to_top(node)
        weight = self.weight
        trace = self.trace
        if swap_op is not None:
            trace += (swap_op,)
            weight += 1
        stack, value = stack.pop()
        assert value == node
        return self._undo_node(stack, set(self.effects_to_undo), trace, weight, node)

    def dedup(self, value: Node, i: int) -> 'SearchState':
        top_index = len(self.stack) - 1
        stack = self.stack
        trace = self.trace
        weight = self.weight
        if i != top_index:
            depth = top_index - i
            stack, op = stack.swap(depth)
            trace += (op,)
            weight += 1
        # TODO: Dedup based on first index within 16 range
        dedup_index = stack.values.index(value)
        assert dedup_index != top_index
        stack, popped_value = stack.pop()
        assert popped_value == value
        dup_depth = len(stack) - dedup_index
        assert dup_depth in range(1, MAX_DUP + 1)
        trace += (f'dup{dup_depth}', )

        return SearchState(
            stack,
            self.effects_to_undo,
            trace,
            weight
        )

    @classmethod
    def _undo_node(
        cls,
        stack: Stack,
        effects_to_undo: set[Node],
        trace: Trace,
        weight: int,
        node: Node
    ) -> 'SearchState':
        stack = stack.push_operands_onto(node)
        if node.operands and stack.peek().name == EFFECT_WRAPPER_NODE:
            stack, top = stack.pop()
            for new_effect in top.operands:
                assert new_effect not in effects_to_undo
                effects_to_undo.add(new_effect)
        trace += (node.name,)
        return SearchState(stack, frozenset(effects_to_undo), trace, weight)


MAX_WEIGHT = 10


def node_post_effects(name: str, *operands: Node, effects: Optional[Sequence[Node]] = None) -> Node:
    if effects is None or not effects:
        return Node(name, *operands)
    return Node(name, Node(EFFECT_WRAPPER_NODE, *effects), *operands)


class Scheduler:
    target_input_symbols: list[str]
    input_value_counts: Counter[str]
    input_value_counts_frozen: frozenset[tuple[str, int]]
    best_solution: Optional[Solution] = None

    def __init__(
        self,
        target_input_symbols: list[str],
        start_output_stack: list[Node],
        start_done_effects: list[Node]
    ) -> None:
        # TODO: Validate no target symbols in effects or output stack nodes

        self.target_input_symbols = target_input_symbols
        self.input_value_counts = Counter(target_input_symbols)
        self.input_value_counts_frozen = frozenset(
            self.input_value_counts.items()
        )

        self.search(SearchState(
            Stack(tuple(start_output_stack)),
            frozenset(start_done_effects)
        ))

    def search(self, state: SearchState):
        if not self.weight_better(state.weight):
            return
        if self.found_input(state):
            self.complete_and_record(state)
            return

        for state in self.next_states(state):
            try:
                self.search(state)
            except RecursionError:
                log.error(
                    f'received recursion error (final state: {state})'
                )
                raise Exception('caught recursion error')

    def next_states(self, state: SearchState) -> Generator[SearchState, None, None]:
        log.debug(f'Getting next states from: {state}')

        # Undo Effect
        for effect in state.effects_to_undo:
            log.debug(f'undoing effect {effect}')
            yield state.undo_effect(effect)

        # Undo Node
        for value in state.stack:
            if value.name in self.target_input_symbols:
                continue
            if state.stack.count(value) > 1:
                continue
            if state.has_dependency(value):
                continue
            log.debug(f'undoing node {value}')
            yield state.undo_node(value)

        # Undo Dup
        for i, value in enumerate(state.stack):
            count = state.stack.count(value)
            if count == 1:
                # log.debug(f'No values to dedup for {value} at {i}')
                continue
            if self.input_value_counts[value.name] >= count:
                continue
            if state.has_dependency(value):
                continue
            log.debug(f'deduping {value} at index {i}')
            yield state.dedup(value, i)

        log.debug(f'End of next states')
        # TODO: pops

    def found_input(self, state: SearchState) -> bool:
        if state.effects_to_undo or len(state.stack) != len(self.target_input_symbols):
            return False

        state_value_counts: Counter[str] = Counter(map(
            lambda node: node.name,
            state.stack
        ))

        return frozenset(state_value_counts.items()) == self.input_value_counts_frozen

    def complete_and_record(self, state: SearchState):
        weight = state.weight
        steps: list[str] = []
        for swap_index in get_swaps(self.target_input_symbols[::-1], [value.name for value in state.stack][::-1]):
            steps.append(f'swap{swap_index}')
            log.debug(f'appended step {steps[-1]}')
            if not self.weight_better(weight := weight + 1):
                return

        assert self.weight_better(weight)

        steps.extend(state.trace[::-1])

        solution = Solution(weight, steps)
        if self.best_solution is None:
            log.info(f'Found first solution ({solution})')

        self.best_solution = solution

    def weight_better(self, weight: int) -> bool:
        return (self.best_solution is None or self.best_solution.weight > weight) and weight <= MAX_WEIGHT
