from collections import Counter
from typing import Generator, Optional, Sequence
from attrs import frozen
from .node import Node
from .stack import Stack
from .logging import log
from .swap import get_swaps


Trace = tuple[str, ...]

MAX_DUP = 16
EFFECT_WRAPPER_NODE = '__effect__'


@frozen
class SearchState:
    stack: Stack
    effects_to_undo: tuple[Node, ...]
    trace: Trace = tuple()
    weight: int = 0

    def undo_effect(self, effect: Node) -> 'SearchState':

        assert effect in self.effects_to_undo
        i = self.effects_to_undo.index(effect)
        new_effects = self.effects_to_undo[:i] + self.effects_to_undo[i+1:]

        return self._undo_node(
            self.stack,
            new_effects,
            self.trace,
            self.weight,
            effect
        )

    def has_dependency(self, node: Node) -> bool:
        return not node.is_constant and any(
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
        return self._undo_node(stack, self.effects_to_undo, trace, weight, node)

    def dedup(self, value: Node, depth: int) -> 'SearchState':
        log.debug(f'Deduping {value} ({depth}) from {self.stack.values}')
        stack = self.stack
        trace = self.trace
        weight = self.weight
        if depth != 0:
            stack, op = stack.swap(depth)
            trace += (op,)
            weight += 1
        # TODO: Dedup based on first index within 16 range
        dedup_index = stack.values.index(value)
        assert dedup_index != len(self.stack) - 1
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
        effects_to_undo: tuple[Node, ...],
        trace: Trace,
        weight: int,
        node: Node
    ) -> 'SearchState':
        stack = stack.push_operands_onto(node)
        if node.operands and stack.peek().name == EFFECT_WRAPPER_NODE:
            stack, top = stack.pop()
            for new_effect in top.operands:
                assert new_effect not in effects_to_undo
                effects_to_undo += (new_effect,)
        trace += (node.name,)
        return SearchState(stack, effects_to_undo, trace, weight)


def node_post_effects(name: str, *operands: Node, effects: Optional[Sequence[Node]] = None) -> Node:
    if effects is None or not effects:
        return Node(name, *operands)
    return Node(name, Node(EFFECT_WRAPPER_NODE, *effects), *operands)


class Scheduler:
    target_input_symbols: list[str]
    input_value_counts: Counter[str]
    input_value_counts_frozen: frozenset[tuple[str, int]]
    best_weight: Optional[int] = None
    best_solutions: list[list[str]]
    optimum_upper_bound: Optional[int]

    def __init__(
        self,
        target_input_symbols: list[str],
        start_output_stack: list[Node],
        start_done_effects: list[Node],
        optimum_upper_bound: Optional[int]
    ) -> None:
        # TODO: Validate no target symbols in effects or output stack nodes

        self.target_input_symbols = target_input_symbols
        self.input_value_counts = Counter(target_input_symbols)
        self.input_value_counts_frozen = frozenset(
            self.input_value_counts.items()
        )
        self.best_solutions = []
        self.optimum_upper_bound = optimum_upper_bound

        self.search(SearchState(
            Stack(tuple(start_output_stack)),
            tuple(start_done_effects)
        ))

    def search(self, state: SearchState):
        if not self.weight_better(state.weight):
            return
        if self.found_input(state):
            self.complete_and_record(state)
            return

        for new_state in self.next_states(state):
            if new_state is not None:
                self.search(new_state)

    def next_states(self, state: SearchState) -> Generator[Optional[SearchState], None, None]:
        log.debug(f'Getting next states from: {state}')

        if self.is_optimal():
            return

        # Undo dup top of stack
        if (top := state.stack.peek()) is not None:
            yield self.undo_dup(state, top, 0)
            yield self.undo_node(state, top)

        # Undo Effect
        for effect in state.effects_to_undo:
            log.debug(f'undoing effect {effect}')
            yield state.undo_effect(effect)

        # Undo Node
        for value in state.stack.tail():
            yield self.undo_node(state, value)

        # Undo Dup
        for depth, node in enumerate(reversed(state.stack.tail()), start=1):
            if (next_state := self.undo_dup(state, node, depth)) is not None:
                yield next_state

        log.debug(f'End of next states')
        # TODO: pops

    def undo_node(self, state: SearchState, value: Node) -> Optional[SearchState]:
        if value.name in self.target_input_symbols:
            return None
        if not value.is_constant and state.stack.count(value) > 1:
            return None
        if state.has_dependency(value):
            return None
        log.debug(f'undoing node {value}')
        return state.undo_node(value)

    def undo_dup(self, state: SearchState, node: Node, depth: int) -> Optional[SearchState]:
        if node.is_constant:
            return None
        count = state.stack.count(node)
        if count == 1:
            return None
        if self.input_value_counts[node.name] >= count:
            return None
        if state.has_dependency(node):
            return None
        log.debug(f'deduping {node} at depth {depth}')
        return state.dedup(node, depth)

    def found_input(self, state: SearchState) -> bool:
        if state.effects_to_undo or len(state.stack) != len(self.target_input_symbols):
            return False

        state_value_counts: Counter[str] = Counter(map(
            lambda node: node.name,
            state.stack
        ))

        return frozenset(state_value_counts.items()) == self.input_value_counts_frozen

    def is_optimal(self) -> bool:
        return self.optimum_upper_bound is not None\
            and self.best_weight is not None\
            and self.best_weight <= self.optimum_upper_bound

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

        if self.best_weight is None or self.best_weight > weight:
            self.best_weight = weight
            self.best_solutions = [steps]
        else:
            assert self.best_weight == weight
            self.best_solutions.append(steps)

        log.info(
            f'New solution (weight: {weight},)\n  steps: {" ".join(steps)}'
        )

    def weight_better(self, weight: int) -> bool:
        return self.best_weight is None or self.best_weight > weight
