from scheduler.node import enode, const
from scheduler.dijkstra import DijkstraSchedule
import sys
import cProfile


def _erc20_example() -> DijkstraSchedule:
    frm = enode('calldataload', const('0x04'))
    to = enode('calldataload', const('0x24'))
    amt = enode('calldataload', const('0x44'))
    error = enode('error')

    from_bal = enode('sload', frm, post=[])
    new_from_bal = enode('sub', from_bal, amt)

    assert new_from_bal.has_dependency(amt.node)

    from_bal_update = enode('sstore', frm, new_from_bal)

    to_bal = enode('sload', to, post=[from_bal_update])
    new_to_bal = enode('add', to_bal, amt)
    to_bal_update = enode('sstore', to, new_to_bal)

    from_bal_too_small = enode('gt', amt, from_bal)
    updated_error = enode('or', from_bal_too_small, error)
    combined_assert = enode('assertFalse', updated_error)

    # store_amt = enode('mstore', const('zero'), amt)
    # log = enode('log3', const('zero'), const('msize'),
    #             const('transfer_event_sig'), frm, to, post=[store_amt])

    store_one = enode('mstore', const('zero'), const('0x01'),
                      post=[combined_assert, to_bal_update])
    return_one = enode(
        'return',
        const('zero'),
        const('msize'),
        post=[store_one]
    )

    return DijkstraSchedule(
        [error.name],
        [],
        [return_one],
    )


def _existing_vars_op_example() -> DijkstraSchedule:
    a, b, c, d = map(enode, 'abcd')
    mstore = enode('mstore', a, b)
    pop_c = enode('pop', c)

    return DijkstraSchedule(
        [*'abcd'],
        [a, b, d],
        [mstore, pop_c]
    )


def _simple_store() -> DijkstraSchedule:
    to = enode('to')
    mod = enode('mod', to)
    store = enode('store', to, mod)

    return DijkstraSchedule(
        [],
        [],
        [store]
    )


def _weth_withdraw_example() -> DijkstraSchedule:
    frm = const('caller')
    to = enode('calldataload', const('0x04'))
    amt = enode('calldataload', const('0x24'))
    error = enode('error')

    bal = enode('sload', frm)
    new_bal = enode('sub', bal, amt)
    update_bal = enode('sstore', frm, new_bal)

    updated_error = enode('or', error, enode('gt', amt, bal))
    check_error = enode('assertFalse', updated_error)

    suc = enode(
        'call',
        const('gas'),
        to,
        amt,
        const('zero'),
        const('zero'),
        const('zero'),
        const('zero'),
        post=[check_error, update_bal]
    )

    bubble = enode('bubble_revert', suc)

    end = enode('stop', post=[bubble])

    return DijkstraSchedule(
        [error.name],
        [],
        [end]
    )


def main():
    scheduler = _erc20_example()
    # scheduler = _weth_withdraw_example()
    # scheduler = _existing_vars_op_example()
    # scheduler = _simple_store()

    assert scheduler.solution, f'No solutions'

    print(f'weight: {scheduler.best_weight}')
    print(f'input stack: {scheduler.target_input_symbols}\n')

    for solution in scheduler.solution:
        print(solution)


if __name__ == '__main__':
    if '--profile' in sys.argv:
        cProfile.run('main()', sort='cumtime')
    else:
        main()
