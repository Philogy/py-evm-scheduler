from scheduler.node import lit
from scheduler.exhaustive_single import schedule_exhaustive_single, show_schedule


def main():
    one = lit('1')
    pure = lit('pure')
    end = lit('end')
    allowed = lit('allowed')
    zero = lit('0')
    offset = lit('offset')

    table = lit('table')

    byte = lit('byte', zero, lit('mload', offset))
    updated_pure = lit(
        'and',
        pure,
        lit('shr', byte, allowed)
    )
    new_offset = lit(
        'add',
        lit('add', offset, one),
        lit('byte', lit('sub', byte, lit('0x60')), table)
    )

    schedule = schedule_exhaustive_single(
        (one, pure, end, allowed, zero, offset),
        (one, updated_pure, end, allowed, zero, new_offset),
        tuple(),
        # target_weight=9,
        # verbose=True
    )

    show_schedule(schedule)

    return
    sel = lit('sel')
    fn = lit('fn')
    wrong_sel = lit('sub', sel, fn)
    amount = lit('amount')
    to = lit('to')
    frm = lit('frm')
    bal_frm = lit('load', frm)

    wrong_bal = lit('gt', amount, bal_frm)
    error = wrong_bal

    bal_to = lit('load', to)

    stack_in = tuple()
    # stack_in = sel,
    schedule = schedule_exhaustive_single(
        stack_in,
        tuple(),
        (
            lit('store', frm, lit('sub', bal_frm, amount)),
            lit('store', to, lit('add', bal_to, amount)),
            lit('assert_false', error),
        )
    )
    print('            ', stack_in)
    show_schedule(schedule)

    # schedule_exhaustive_single(
    #     stack_in=tuple(),
    #     stack_out=(x, x),
    #     effects=tuple()
    # )


if __name__ == '__main__':
    main()
