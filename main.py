from scheduler.graph import Graph
from scheduler.node import Node, lit
from scheduler.exhaustive_single import schedule_exhaustive_single, show_schedule


def main():
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
