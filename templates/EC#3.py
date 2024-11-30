import random
import time
import matplotlib.pyplot as plt

class Heap:
    """
    Object to represent a heap
    - internally keeps track of array A
    - array can be referenced with self.A
    """

    def __init__(self, A):
        #####################
        ### DO NOT MODIFY ###
        #####################
        self.A = A
        self.heap_size = len(A)

    @staticmethod
    def parent(i):
        # Return the index of the parent
        return (i - 1) // 2

    @staticmethod
    def left(i):
        # Return the index of the left child
        return 2 * i + 1

    @staticmethod
    def right(i):
        # Return the index of the right child
        return 2 * i + 2

    def max_heapify(self, i):
        # Keep the heap property
        left = Heap.left(i)
        right = Heap.right(i)
        largest = i

        if left < self.heap_size and self.A[left] > self.A[largest]:
            largest = left

        if right < self.heap_size and self.A[right] > self.A[largest]:
            largest = right

        if largest != i:
            self.exchange(i, largest)
            self.max_heapify(largest)

    def build_max_heap(self):
        # Convert array into a max-heap
        self.heap_size = len(self.A)
        for i in range(self.heap_size // 2 - 1, -1, -1):
            self.max_heapify(i)

    def heapsort(self):
        # Sorts the array using heap sort
        self.build_max_heap()
        for i in range(len(self.A) - 1, 0, -1):
            self.exchange(0, i)
            self.heap_size -= 1
            self.max_heapify(0)

    def exchange(self, i, j):
        #####################
        ### DO NOT MODIFY ###
        #####################
        self.A[i], self.A[j] = self.A[j], self.A[i]

    def __str__(self):
        #####################
        ### DO NOT MODIFY ###
        #####################
        return str(self.A)

def generate_figures():
    # Measure the runtime of each sorting algorithm
    sizes = [10, 50, 100, 500, 1000, 5000, 10000]
    heap_times = []
    insertion_times = []
    merge_times = []

    for size in sizes:
        arr = [random.randint(0, size) for _ in range(size)]

        # Heapsort time
        heap = Heap(arr.copy())
        start_time = time.time()
        heap.heapsort()
        heap_times.append(time.time() - start_time)

        # Insertion sort time
        arr_copy = arr.copy()
        start_time = time.time()
        insertion_sort(arr_copy)
        insertion_times.append(time.time() - start_time)

        # Merge sort time
        arr_copy = arr.copy()
        start_time = time.time()
        merge_sort(arr_copy)
        merge_times.append(time.time() - start_time)

    # result plots below
    plt.plot(sizes, heap_times, label='Heapsort')
    plt.plot(sizes, insertion_times, label='Insertion Sort')
    plt.plot(sizes, merge_times, label='Merge Sort')
    plt.xlabel('Array Size')
    plt.ylabel('Time (seconds)')
    plt.legend()
    plt.title('Sorting Algorithm Performance Comparison')
    plt.show()

def test_heapsort(
    n=10000,
    min_array_size=0,
    max_array_size=100,
    min_array_value=-50,
    max_array_value=50
):
    #####################
    ### DO NOT MODIFY ###
    #####################
    num_failed = 0
    for _ in range(n):
        array_size = random.randint(min_array_size, max_array_size)
        a = [random.randint(min_array_value, max_array_value) for _ in range(array_size)]
        heap = Heap(a.copy())
        heap.heapsort()
        a.sort()
        if a != heap.A:
            num_failed += 1
            print("Expected:", a)
            print("Got:", heap.A)
    if num_failed == 0:
        print(f'Passed all {n} tests!')
    else:
        print(f'Failed {num_failed} out of {n} tests!!!')

#########################################################
#### Provided Working Insertion Sort and Merge Sort ####
#########################################################
def insertion_sort(arr):
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key

def merge_sort(arr):
    merge_sort_helper(arr, 0, len(arr) - 1)

def merge_sort_helper(arr, left_index, right_index):
    if left_index >= right_index:
        return
    mid_index = (left_index + right_index) // 2
    merge_sort_helper(arr, left_index, mid_index)
    merge_sort_helper(arr, mid_index + 1, right_index)
    merge(arr, left_index, mid_index, right_index)

def merge(arr, left_index, mid_index, right_index):
    left = arr[left_index:mid_index + 1]
    right = arr[mid_index + 1:right_index + 1]
    i = j = 0
    k = left_index
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            arr[k] = left[i]
            i += 1
        else:
            arr[k] = right[j]
            j += 1
        k += 1
    while i < len(left):
        arr[k] = left[i]
        i += 1
        k += 1
    while j < len(right):
        arr[k] = right[j]
        j += 1
        k += 1

if __name__ == '__main__':
    A = [2, 7, 3, 9, 4]
    heap = Heap(A)
    heap.heapsort()
    print('Sorted Array:', heap.A)
    test_heapsort()
    generate_figures()  
