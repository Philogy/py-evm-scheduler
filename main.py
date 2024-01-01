from scheduler.node import lit
from scheduler.exhaustive_single import schedule_exhaustive_single, show_schedule

'''
stack:           [from: 2, to: 2, wad: 3]
=> from_bal, many dependents, base of tree
dup1          // [from: 1, to: 2, wad: 2, wad: 1, from_bal: 2]
dup4 load     // [from: 1, to: 2, wad: 3, wad: 1, from_bal: 2]
=> check_from_bal can be scheduled rn with no swaps
dup1          // [from: 1, to: 2, wad: 3, wad: 1, from_bal: 1, from_bal: 1]
dup3          // [from: 1, to: 2, wad: 2, wad: 1, from_bal: 1, from_bal: 1, wad: 1]
gt            // [from: 1, to: 2, wad: 2, wad: 1, from_bal: 1, wad > from_bal: 1]
assert_false  // [from: 1, to: 2, wad: 2, wad: 1, from_bal: 1]
=> update_from_bal
sub           // [from: 1, to: 2, wad: 1, from_bal - wad: 1]
swap1         // [from: 1, to: 2, from_bal - wad: 1, wad: 1]
swap3         // [wad: 1, to: 2, from_bal - wad: 1, from: 1]
sstore        // [wad: 1, to: 2]





'''

'''
              // [wad: 1, to: 2, from_bal - wad: 1, from: 1]
swap1         // [wad: 1, to: 2, from: 1, from_bal - wad: 1]
sub           // [wad: 1, to: 2, from: 1, wad: 1, from_bal: 1]
...           // [wad: 1, to: 2, from: 1, wad: 1, from_bal: 2]
load          // [wad: 1, to: 2, from: 1, wad: 1, from: 1]
dup2          // [wad: 1, to: 2, from: 1, wad: 1]

'''


def main():
    frm, to, wad = map(lit, ['frm', 'to', 'wad'])

    from_bal = lit('load', frm)
    update_from_bal = lit('sstore', frm, lit('sub', from_bal, wad))
    to_bal = lit('load', to)
    update_to_bal = lit('sstore', to, lit('add', to_bal, wad))
    check_from_bal = lit('assert_false', lit('gt', wad, from_bal))

    # a = lit('A', x, y)
    # b = lit('B', x, z)
    # c = lit('C', a, b)

    stack_in = frm, to, wad
    schedule = schedule_exhaustive_single(
        stack_in,
        tuple(),
        (update_from_bal, update_to_bal, check_from_bal)
    )
    print(list(stack_in))
    show_schedule(schedule)


if __name__ == '__main__':
    main()
'''
      // [a, b, c]
swap1 // [a, c, b]
swap2 // [b, c, a]
swap1 // [b, a, c]
swap2 // [c, a, b]
swap1 // [c, b, a]
'''
