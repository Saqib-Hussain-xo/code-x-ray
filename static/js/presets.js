/**
 * X-Ray Execution Agent: Algorithm Preset Library (25 Algorithms)
 * File: static/js/presets.js
 *
 * Provides 25 verified Python algorithms organized across 6 algorithmic domains:
 * - Two Pointers (1-6)
 * - Sliding Window (7-10)
 * - Searching and Arrays (11-15)
 * - Sorting (16-19)
 * - Matrices (20-23)
 * - Stacks, Queues, and Recursion (24-25)
 *
 * Strict engineering constraints:
 * - Pure valid Python, deterministic inputs, bounded step counts (< 100 steps)
 * - Sequence detection and pointer binding supported by ExecutionTracer
 * - Zero em dashes, zero external dependencies, no auto-execution on select
 */

const ALGORITHM_PRESETS = {
    // ==========================================
    // Category 1: Two Pointers
    // ==========================================

    two_pointer_palindrome: `# 1. Palindrome Check
# Two pointers (left, right) converge from both ends of the string
text = "racecar"
left = 0
right = len(text) - 1
is_palindrome = True

while left < right:
    print(f"Comparing text[{left}]='{text[left]}' vs text[{right}]='{text[right]}'")
    if text[left] != text[right]:
        is_palindrome = False
        break
    left += 1
    right -= 1

print(f"Result for '{text}': {is_palindrome}")
`,

    two_sum_sorted: `# 2. Two Sum on Sorted Array
# Two pointers (left, right) adjust based on current sum vs target
nums = [2, 7, 11, 15]
target = 18
left = 0
right = len(nums) - 1
pair = []

while left < right:
    curr_sum = nums[left] + nums[right]
    print(f"left={left}({nums[left]}), right={right}({nums[right]}), sum={curr_sum}")
    if curr_sum == target:
        pair = [left, right]
        break
    elif curr_sum < target:
        left += 1
    else:
        right -= 1

print(f"Target {target} found at indices: {pair}")
`,

    reverse_array: `# 3. Reverse Array In-Place
# Two pointers (left, right) swap outer elements moving inwards
arr = [10, 20, 30, 40, 50]
left = 0
right = len(arr) - 1

while left < right:
    print(f"Swapping arr[{left}]={arr[left]} with arr[{right}]={arr[right]}")
    arr[left], arr[right] = arr[right], arr[left]
    left += 1
    right -= 1

print(f"Reversed array: {arr}")
`,

    remove_duplicates: `# 4. Remove Duplicates from Sorted Array
# Slow pointer tracks unique boundary, fast pointer scans the array
nums = [1, 1, 2, 2, 3, 4, 4]
if len(nums) <= 1:
    length = len(nums)
else:
    slow = 0
    for fast in range(1, len(nums)):
        if nums[fast] != nums[slow]:
            slow += 1
            nums[slow] = nums[fast]
            print(f"Placed {nums[slow]} at unique index slow={slow}")
    length = slow + 1

print(f"Unique count: {length}, unique prefix: {nums[:length]}")
`,

    move_zeroes: `# 5. Move Zeroes
# Shift non-zero elements forward using write/read pointer positions
nums = [0, 1, 0, 3, 12]
write = 0

for read in range(len(nums)):
    if nums[read] != 0:
        if read != write:
            nums[write], nums[read] = nums[read], nums[write]
            print(f"Swapped non-zero {nums[write]} to write={write}")
        write += 1

print(f"Array with zeroes moved: {nums}")
`,

    container_most_water: `# 6. Container With Most Water
# Two pointers (left, right) track max water area bounded by shortest height
heights = [1, 8, 6, 2, 5, 4, 8, 3]
left = 0
right = len(heights) - 1
max_area = 0

while left < right:
    h = min(heights[left], heights[right])
    w = right - left
    area = h * w
    if area > max_area:
        max_area = area
    print(f"left={left}, right={right}, h={h}, w={w}, area={area}, max={max_area}")
    if heights[left] < heights[right]:
        left += 1
    else:
        right -= 1

print(f"Maximum water area: {max_area}")
`,

    // ==========================================
    // Category 2: Sliding Window
    // ==========================================

    max_sum_subarray: `# 7. Maximum Sum Subarray (Fixed Window k = 3)
nums = [2, 1, 5, 1, 3, 2]
k = 3
window_sum = sum(nums[:k])
max_sum = window_sum
start = 0

for end in range(k, len(nums)):
    window_sum += nums[end] - nums[start]
    if window_sum > max_sum:
        max_sum = window_sum
    print(f"Window [{start+1}..{end}]: sum={window_sum}, max={max_sum}")
    start += 1

print(f"Max window sum: {max_sum}")
`,

    min_length_subarray: `# 8. Minimum-Length Subarray Sum >= S
nums = [2, 3, 1, 2, 4, 3]
target = 7
start = 0
curr_sum = 0
min_len = len(nums) + 1

for end in range(len(nums)):
    curr_sum += nums[end]
    while curr_sum >= target:
        window_len = end - start + 1
        if window_len < min_len:
            min_len = window_len
        print(f"Valid window [{start}..{end}] sum={curr_sum}, len={window_len}")
        curr_sum -= nums[start]
        start += 1

result = min_len if min_len <= len(nums) else 0
print(f"Minimum subarray length for target {target}: {result}")
`,

    longest_substr_no_repeat: `# 9. Longest Substring Without Repeating Characters
text = "abcabcbb"
char_index = {}
start = 0
max_len = 0
longest_sub = ""

for end in range(len(text)):
    c = text[end]
    if c in char_index and char_index[c] >= start:
        start = char_index[c] + 1
    char_index[c] = end
    curr_len = end - start + 1
    if curr_len > max_len:
        max_len = curr_len
        longest_sub = text[start:end+1]
    print(f"end={end}('{c}'), start={start}, window='{text[start:end+1]}', max={max_len}")

print(f"Longest non-repeating substring: '{longest_sub}' (len: {max_len})")
`,

    fixed_window_average: `# 10. Fixed-Size Window Average
readings = [10, 20, 30, 40, 50, 60]
k = 3
averages = []
curr_sum = sum(readings[:k])
averages.append(curr_sum / k)
start = 0

for end in range(k, len(readings)):
    curr_sum += readings[end] - readings[start]
    avg = curr_sum / k
    averages.append(avg)
    print(f"Window [{start+1}..{end}]: sum={curr_sum}, avg={avg:.2f}")
    start += 1

print(f"Moving averages: {averages}")
`,

    // ==========================================
    // Category 3: Searching and Arrays
    // ==========================================

    linear_search: `# 11. Linear Search
nums = [4, 2, 9, 7, 5, 8]
target = 7
found_idx = -1

for i in range(len(nums)):
    val = nums[i]
    print(f"Inspecting index i={i}, val={val}")
    if val == target:
        found_idx = i
        print(f"Target {target} located at index {i}")
        break

print(f"Linear search result: index {found_idx}")
`,

    binary_search: `# 12. Binary Search on Sorted Array
nums = [2, 5, 8, 12, 16, 23, 38, 45, 56, 72]
target = 23
low = 0
high = len(nums) - 1
found_idx = -1

while low <= high:
    mid = (low + high) // 2
    print(f"low={low}, high={high}, mid={mid}, nums[mid]={nums[mid]}")
    if nums[mid] == target:
        found_idx = mid
        print(f"Match found at mid={mid}")
        break
    elif nums[mid] < target:
        low = mid + 1
    else:
        high = mid - 1

print(f"Target {target} index: {found_idx}")
`,

    sentinel_search: `# 13. Sentinel Linear Search
values = [14, 28, 56, 42, 70]
target = 42
n = len(values)
last = values[-1]
values[-1] = target
i = 0

while values[i] != target:
    i += 1

values[-1] = last
found = (i < n - 1) or (last == target)
print(f"Target {target} found at index {i}: {found}")
`,

    prefix_sums: `# 14. Prefix Sums Array
nums = [3, 1, 4, 1, 5, 9]
prefix = [0] * (len(nums) + 1)

for i in range(len(nums)):
    prefix[i + 1] = prefix[i] + nums[i]
    print(f"prefix[{i+1}] = prefix[{i}] + nums[{i}] = {prefix[i+1]}")

print(f"Original: {nums}")
print(f"Prefix sums: {prefix}")
sub_sum = prefix[4] - prefix[1]
print(f"Sum of nums[1..3]: {sub_sum}")
`,

    frequency_counting: `# 15. Frequency Counting
items = ["apple", "banana", "apple", "cherry", "banana", "apple"]
counts = {}

for idx in range(len(items)):
    fruit = items[idx]
    counts[fruit] = counts.get(fruit, 0) + 1
    print(f"Processed items[{idx}]='{fruit}', count={counts[fruit]}")

print(f"Final frequencies: {counts}")
`,

    // ==========================================
    // Category 4: Sorting
    // ==========================================

    bubble_sort: `# 16. Bubble Sort
arr = [5, 1, 4, 2, 8]
n = len(arr)

for i in range(n):
    swapped = False
    for j in range(0, n - i - 1):
        print(f"Comparing arr[{j}]={arr[j]} and arr[{j+1}]={arr[j+1]}")
        if arr[j] > arr[j + 1]:
            arr[j], arr[j + 1] = arr[j + 1], arr[j]
            swapped = True
            print(f"  Swapped: {arr}")
    if not swapped:
        break

print(f"Sorted array: {arr}")
`,

    selection_sort: `# 17. Selection Sort
arr = [29, 10, 14, 37, 13]
n = len(arr)

for i in range(n):
    min_idx = i
    for j in range(i + 1, n):
        if arr[j] < arr[min_idx]:
            min_idx = j
    if min_idx != i:
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
        print(f"Step {i}: swapped min {arr[i]} into index {i}: {arr}")

print(f"Sorted array: {arr}")
`,

    insertion_sort: `# 18. Insertion Sort
arr = [12, 11, 13, 5, 6]

for i in range(1, len(arr)):
    key = arr[i]
    j = i - 1
    print(f"Inserting key={key} from index i={i}")
    while j >= 0 and arr[j] > key:
        arr[j + 1] = arr[j]
        j -= 1
    arr[j + 1] = key
    print(f"  Array after pass {i}: {arr}")

print(f"Sorted array: {arr}")
`,

    merge_sort: `# 19. Iterative Two-Way Merge
left_arr = [2, 5, 9]
right_arr = [1, 4, 8, 10]
merged = []
i = 0
j = 0

while i < len(left_arr) and j < len(right_arr):
    if left_arr[i] <= right_arr[j]:
        merged.append(left_arr[i])
        print(f"Appended left_arr[{i}]={left_arr[i]}")
        i += 1
    else:
        merged.append(right_arr[j])
        print(f"Appended right_arr[{j}]={right_arr[j]}")
        j += 1

while i < len(left_arr):
    merged.append(left_arr[i])
    i += 1

while j < len(right_arr):
    merged.append(right_arr[j])
    j += 1

print(f"Merged sorted array: {merged}")
`,

    // ==========================================
    // Category 5: Matrices
    // ==========================================

    matrix_traversal: `# 20. Nested Matrix Traversal
matrix = [
    [1, 2, 3],
    [4, 5, 6]
]
total = 0

for i in range(len(matrix)):
    for j in range(len(matrix[i])):
        val = matrix[i][j]
        total += val
        print(f"matrix[{i}][{j}] = {val}, total = {total}")

print(f"Matrix sum: {total}")
`,

    matrix_row_sums: `# 21. Row Sums
grid = [
    [3, 5, 2],
    [8, 1, 4],
    [7, 6, 9]
]
row_sums = []

for i in range(len(grid)):
    curr_sum = 0
    for j in range(len(grid[i])):
        curr_sum += grid[i][j]
    row_sums.append(curr_sum)
    print(f"Row {i} sum: {curr_sum}")

print(f"All row sums: {row_sums}")
`,

    matrix_col_sums: `# 22. Column Sums
grid = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
num_cols = len(grid[0])
col_sums = [0] * num_cols

for j in range(num_cols):
    curr_sum = 0
    for i in range(len(grid)):
        curr_sum += grid[i][j]
    col_sums[j] = curr_sum
    print(f"Column {j} sum: {curr_sum}")

print(f"All column sums: {col_sums}")
`,

    matrix_diagonal: `# 23. Diagonal Traversal
sq_matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
n = len(sq_matrix)
main_diag = []
anti_diag = []

for i in range(n):
    main_val = sq_matrix[i][i]
    anti_val = sq_matrix[i][n - 1 - i]
    main_diag.append(main_val)
    anti_diag.append(anti_val)
    print(f"i={i}: main diag={main_val}, anti diag={anti_val}")

print(f"Main diagonal: {main_diag}")
print(f"Anti diagonal: {anti_diag}")
`,

    // ==========================================
    // Category 6: Stacks, Queues, and Recursion
    // ==========================================

    stack_queue_ops: `# 24. Stack and Queue Operations
stack = []
queue = []

# Stack operations (LIFO)
for item in [10, 20, 30]:
    stack.append(item)
    print(f"Pushed to stack: {item}, current stack={stack}")

popped_stack = stack.pop()
print(f"Popped from stack: {popped_stack}, remaining={stack}")

# Queue operations (FIFO)
for item in ["alpha", "beta", "gamma"]:
    queue.append(item)
    print(f"Enqueued: {item}, queue={queue}")

dequeued = queue.pop(0)
print(f"Dequeued: {dequeued}, remaining={queue}")
`,

    factorial_fibonacci: `# 25. Factorial and Fibonacci Recursion
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)

fact_4 = factorial(4)
print(f"factorial(4) = {fact_4}")

fib_5 = fibonacci(5)
print(f"fibonacci(5) = {fib_5}")
`
};

// Expose globally on window
if (typeof window !== "undefined") {
    window.ALGORITHM_PRESETS = ALGORITHM_PRESETS;
}
