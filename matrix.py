import numpy as np
from numpy.typing import NDArray


def stack_to_matrix(nums: list[int]) -> NDArray[np.ulonglong]:
    arr = np.identity(
        len(nums),
        dtype=np.ulonglong
    )
    for i, x in enumerate(nums):
        arr[i, i] = x
    return arr


def swap(size: int, n: int) -> NDArray[np.ulonglong]:
    arr = np.zeros((size, size), dtype=np.ulonglong)
    for i in range(size):
        if i in (0, n):
            arr[i, n - i] = 1
        else:
            arr[i, i] = 1
    return arr


def dup(size: int, n: int) -> NDArray[np.ulonglong]:


def matrix_to_stack(arr: NDArray[np.ulonglong]) -> list[int]:
    return list(arr.sum(axis=0))


def main():
    # stack_in = [* range(4)]
    # s = stack_to_matrix(stack_in)
    # swap1 = swap(4, 1)
    # swap2 = swap(4, 2)
    # swap3 = swap(4, 3)

    # comb = swap2.dot(swap1)
    # print(comb)
    # out = s.dot(comb)
    # print(stack_in)
    # print(matrix_to_stack(out))
    dup1 = np.array([
        [1, 1, 1],
        [0, 0, 0],
        [0, 0, 0]
    ])
    print(np.array([
        [0, 0, 0],
        [1, 0, 0],
        [0, 1, 0]
    ]).dot(dup1).dot(dup1))


if __name__ == '__main__':
    main()
