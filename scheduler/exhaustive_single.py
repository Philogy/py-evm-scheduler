from typing import Generator, NamedTuple, Optional, TypeVar
from .node import Node


Stack = tuple[Node, ...]


def weight_of(schedule: tuple[str, ...]) -> int:
    return sum(
        step.startswith('dup') or step.startswith('swap')
        for step in schedule
    )


def show_schedule(schedule: tuple[str, ...]):
    max_len = max([
        len(s.split(' ', 1)[0])
        for s in schedule
    ])
    for s in schedule:
        action, stack = s.split(' ', 1)
        print(action + ' ' * (2 + max_len - len(action)) + stack)


class SearchResult:
    best: Optional[int]
    schedule: Optional[tuple[str, ...]]

    def __init__(self):
        self.best = None
        self.schedule = None

    def record_new(self, schedule: tuple[str, ...]):
        weight = weight_of(schedule)
        if self.best is None or weight < self.best:
            self.best = weight
            self.schedule = schedule

    def not_candidate(self, schedule: tuple[str, ...]) -> bool:
        if self.best is None:
            return False
        return weight_of(schedule) >= self.best


class ScheduleState(NamedTuple(
    'ScheduleState',
    [
        ('stack', Stack),
        ('effects', tuple[Node, ...])
    ],

)):
    def set_stack(self, new_stack: Stack) -> 'ScheduleState':
        return ScheduleState(new_stack, self.effects)


T = TypeVar('T')


def remove(tup: tuple[T, ...], i: int) -> tuple[T, ...]:
    return tup[:i] + tup[i+1:]


def undo_onto_stack(stack: Stack, node: Node) -> Stack:
    for operand in node.operands[::-1]:
        stack += operand,
    return stack


StateTrans = Optional[tuple[ScheduleState, str]]


def undo_top(state: ScheduleState) -> StateTrans:
    top = state.stack[-1]
    if any(value.has_dep(top) for value in state.stack[:-1]):
        return None
    new_stack = undo_onto_stack(state.stack[:-1], top)
    return state.set_stack(new_stack), f'{top.name}'


def undo_effect(state: ScheduleState, effect_index: int) -> tuple[ScheduleState, str]:
    assert effect_index in range(len(state.effects))
    effect = state.effects[effect_index]
    new_stack = undo_onto_stack(state.stack, effect)
    return ScheduleState(new_stack, remove(state.effects, effect_index)), f'{effect.name}'


def dedup_top(state: ScheduleState, rev_index: int) -> tuple[ScheduleState, str]:
    depth = len(state.stack) - rev_index - 1
    return state.set_stack(state.stack[:-1]), f'dup{depth}'


def swap(state: ScheduleState, depth: int) -> StateTrans:
    new_stack = list(state.stack)
    new_stack[-1], new_stack[-depth-1] = new_stack[-depth-1], new_stack[-1]
    return state.set_stack(tuple(new_stack)), f'swap{depth}'


def get_backwards_paths(state: ScheduleState) -> Generator[StateTrans, None, None]:
    for i, _ in enumerate(state.effects):
        yield undo_effect(state, i)
    if len(state.stack) > 0:
        yield undo_top(state)
        top = state.stack[-1]
        for i, el in enumerate(state.stack[:-1]):
            if el == top:
                yield dedup_top(state, i)
    for depth in range(1, len(state.stack)):
        yield swap(state, depth)


def traverse_backwards(
    result: SearchResult,
    already_traversed: frozenset[ScheduleState],
    entry_point: ScheduleState,
    current: ScheduleState,
    ops: tuple[str, ...]
):
    if result.not_candidate(ops) or current in already_traversed:
        return
    if current == entry_point:
        result.record_new(ops)
        return
    for transition in get_backwards_paths(current):
        if transition is not None:
            new_state, new_op = transition
            traverse_backwards(
                result,
                already_traversed | frozenset({current}),
                entry_point,
                new_state,
                ops + (new_op + ' ' + str(current.stack),)
            )


def schedule_exhaustive_single(
    stack_in: tuple[Node, ...],
    stack_out: tuple[Node, ...],
    effects: tuple[Node, ...]
) -> tuple[str, ...]:
    start = ScheduleState(stack_in, tuple())
    goal = ScheduleState(stack_out, effects)
    result = SearchResult()
    traverse_backwards(
        result,
        frozenset(),
        start,
        goal,
        tuple()
    )
    assert result.schedule is not None
    return result.schedule[::-1]


'''

             (y, z, x)
swap1     3: (y, x, z)
dup2      4: (y, x, z, x)
node(B)   3: (y, x, B(x, z))
swap2     3: (B(x, z), x, y)
swap1     3: (B(x, z), y, x)
node(A)   2: (B(x, z), A(x, y))
node(C)   1: (C(A(x, y), B(x, z)),)

'''
