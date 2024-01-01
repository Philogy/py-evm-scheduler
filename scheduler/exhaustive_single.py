from typing import Generator, NamedTuple, Optional, TypeVar
from collections import defaultdict
from .stack import Stack
from .node import Node, has_dep


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

    def __init__(self, target_weight: Optional[int]):
        self.best = target_weight
        self.schedule = None

    def record_new(self, schedule: tuple[str, ...]):
        if self.is_candidate(schedule):
            print(
                f'found: {" ".join(s.split(" ", 1)[0] for s in schedule[::-1])}'
            )
            self.best = weight_of(schedule)
            self.schedule = schedule

    def is_candidate(self, schedule: tuple[str, ...]) -> bool:
        weight = weight_of(schedule)
        if self.best is None:
            return True
        return weight < self.best


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
        stack = stack.push(operand)
    return stack


StateTrans = Optional[tuple[ScheduleState, str]]


def undo_top(state: ScheduleState) -> StateTrans:
    top, new_stack = state.stack.pop()
    if any(has_dep(value, top) for value in state.stack.values[:-1])\
            or any(has_dep(effect, top) for effect in state.effects):
        return None
    # print(f'undoing {top} ...')
    new_stack = undo_onto_stack(new_stack, top)
    return state.set_stack(new_stack), f'{top.name}'


def undo_effect(state: ScheduleState, effect_index: int) -> StateTrans:
    assert effect_index in range(len(state.effects))
    effect = state.effects[effect_index]
    new_stack = undo_onto_stack(state.stack, effect)
    return ScheduleState(new_stack, remove(state.effects, effect_index)), f'{effect.name}'


def dedup_top(state: ScheduleState, rev_index: int) -> tuple[ScheduleState, str]:
    depth = len(state.stack) - rev_index - 1
    _, new_stack = state.stack.pop()
    return state.set_stack(new_stack), f'dup{depth}'


def swap(state: ScheduleState, depth: int) -> StateTrans:
    return state.set_stack(state.stack.swap(depth)), f'swap{depth}'


def get_backwards_paths(entry_point: ScheduleState, state: ScheduleState) -> Generator[StateTrans, None, None]:
    for i, _ in enumerate(state.effects):
        yield undo_effect(state, i)
    if len(state.stack) > 0:
        top = state.stack.values[-1]
        if top not in entry_point.stack.values:
            yield undo_top(state)
        for i, el in enumerate(state.stack.values[:-1]):
            if el == top:
                yield dedup_top(state, i)
    # print(f'\nstate.stack:')
    # for v in state.stack.values[::-1]:
    #     print(f'    {v}')
    for depth in range(1, len(state.stack)):
        # print(f'swap{depth}')
        yield swap(state, depth)


def traverse_backwards(
    result: SearchResult,
    already_traversed: frozenset[ScheduleState],
    entry_point: ScheduleState,
    current: ScheduleState,
    ops: tuple[str, ...],
    verbose: bool,
    depth: int
):
    # assert len(ops) < 20
    # print(f'\nstack: {current.stack}')
    # for op in ops[::-1]:
    #     print(op)
    padding = ' ' * (2 * depth)
    if not result.is_candidate(ops):
        if verbose:
            print(f'{padding}=> not candidate')
        return
    if current in already_traversed:
        if verbose:
            print(f'{padding}=> already traversed')
        return
    if current == entry_point:
        if verbose:
            print(f'{padding}=> W rizz ({weight_of(ops)})')
        result.record_new(ops)
        return
    # if not current.effects and has_elements()
    new_traversed = already_traversed | frozenset({current})
    for transition in get_backwards_paths(entry_point, current):
        if transition is not None:
            new_state, new_op = transition
            if verbose:
                print(
                    padding
                    + f'└--------> {new_op} => {new_state.stack}'
                )
            traverse_backwards(
                result,
                new_traversed,
                entry_point,
                new_state,
                ops + (new_op + ' ' + str(current.stack),),
                verbose,
                depth + 1
            )


def schedule_exhaustive_single(
    stack_in: tuple[Node, ...],
    stack_out: tuple[Node, ...],
    effects: tuple[Node, ...],
    target_weight: Optional[int] = None,
    verbose: bool = False
) -> tuple[str, ...]:
    start = ScheduleState(Stack(stack_in), tuple())
    goal = ScheduleState(Stack(stack_out), effects)
    result = SearchResult(target_weight)
    if verbose:
        print(goal.stack)
    traverse_backwards(
        result,
        frozenset(),
        start,
        goal,
        tuple(),
        verbose=verbose,
        depth=0
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
