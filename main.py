from scheduler.node import Node
from scheduler.schedule import Scheduler, node_post_effects


def _erc20_example():
    # frm = Node('calldataload', Node.lit('0x04'), alias='from')
    # to = Node('calldataload', Node.lit('0x24'), alias='to')
    # amt = Node('calldataload', Node.lit('0x44'), alias='amount')
    frm = Node.lit('frm')
    to = Node.lit('to')
    amt = Node.lit('amt')
    dispatch_error = Node.lit('dispatch_error')

    from_bal = node_post_effects('sload', frm, effects=[])
    new_from_bal = Node('sub', from_bal, amt)
    from_bal_update = Node('sstore', frm, new_from_bal)

    to_bal = node_post_effects('sload', to, effects=[from_bal_update])
    new_to_bal = Node('add', to_bal, amt)
    to_bal_update = Node('sstore', to, new_to_bal)

    from_bal_too_small = Node('gt', amt, from_bal)
    updated_error = Node('or', dispatch_error, from_bal_too_small)
    combined_assert = Node('assertFalse', updated_error)

    scheduler = Scheduler(
        [dispatch_error.name],
        [],
        [to_bal_update, combined_assert]
    )

    print(f'scheduler.best_solution: {scheduler.best_solution}')


def main():
    _erc20_example()


if __name__ == '__main__':
    main()

'''
amt             | amt
frm             | amt frm
dup1            | amt frm frm
sload           | amt frm frm_bal
dup3            | amt frm frm_bal amt
to              | amt frm frm_bal amt to
dup5            | amt frm frm_bal amt to amt
dup4            | amt frm frm_bal amt to amt frm_bal
sub             | amt frm frm_bal amt to frm_bal'
dup2            | amt frm frm_bal amt to frm_bal' to
swap5           | amt to frm_bal amt to frm_bal' frm
sstore          | amt to frm_bal amt to
sload           | amt to frm_bal amt to_bal
add             | amt to frm_bal to_bal'
swap3           | to_bal' to frm_bal amt
gt              | to_bal' to bal_too_small
assertFalse     | to_bal' to
sstore          | -
'''
