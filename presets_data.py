"""
X-Ray Execution Agent: Canonical Backend Presets Allowlist
Module: presets_data.py

Canonical backend definition of the 25 verified algorithm presets.
Strictly restricts execution to these pre-audited programs for secure public demo hosting.
"""

from typing import Dict, Any

ALGORITHM_PRESETS: Dict[str, Dict[str, Any]] = {
    'two_pointer_palindrome': {
        "id": 'two_pointer_palindrome',
        "title": '1. Palindrome Check',
        "category": 'Two Pointers',
        "code": '# 1. Palindrome Check\n# Two pointers (left, right) converge from both ends of the string\ntext = "racecar"\nleft = 0\nright = len(text) - 1\nis_palindrome = True\n\nwhile left < right:\n    print(f"Comparing text[{left}]=\'{text[left]}\' vs text[{right}]=\'{text[right]}\'")\n    if text[left] != text[right]:\n        is_palindrome = False\n        break\n    left += 1\n    right -= 1\n\nprint(f"Result for \'{text}\': {is_palindrome}")\n'
    },
    'two_sum_sorted': {
        "id": 'two_sum_sorted',
        "title": '2. Two Sum on Sorted Array',
        "category": 'Two Pointers',
        "code": '# 2. Two Sum on Sorted Array\n# Two pointers (left, right) adjust based on current sum vs target\nnums = [2, 7, 11, 15]\ntarget = 18\nleft = 0\nright = len(nums) - 1\npair = []\n\nwhile left < right:\n    curr_sum = nums[left] + nums[right]\n    print(f"left={left}({nums[left]}), right={right}({nums[right]}), sum={curr_sum}")\n    if curr_sum == target:\n        pair = [left, right]\n        break\n    elif curr_sum < target:\n        left += 1\n    else:\n        right -= 1\n\nprint(f"Target {target} found at indices: {pair}")\n'
    },
    'reverse_array': {
        "id": 'reverse_array',
        "title": '3. Reverse Array',
        "category": 'Two Pointers',
        "code": '# 3. Reverse Array In-Place\n# Two pointers (left, right) swap outer elements moving inwards\narr = [10, 20, 30, 40, 50]\nleft = 0\nright = len(arr) - 1\n\nwhile left < right:\n    print(f"Swapping arr[{left}]={arr[left]} with arr[{right}]={arr[right]}")\n    arr[left], arr[right] = arr[right], arr[left]\n    left += 1\n    right -= 1\n\nprint(f"Reversed array: {arr}")\n'
    },
    'remove_duplicates': {
        "id": 'remove_duplicates',
        "title": '4. Remove Duplicates from Sorted Array',
        "category": 'Two Pointers',
        "code": '# 4. Remove Duplicates from Sorted Array\n# Slow pointer tracks unique boundary, fast pointer scans the array\nnums = [1, 1, 2, 2, 3, 4, 4]\nif len(nums) <= 1:\n    length = len(nums)\nelse:\n    slow = 0\n    for fast in range(1, len(nums)):\n        if nums[fast] != nums[slow]:\n            slow += 1\n            nums[slow] = nums[fast]\n            print(f"Placed {nums[slow]} at unique index slow={slow}")\n    length = slow + 1\n\nprint(f"Unique count: {length}, unique prefix: {nums[:length]}")\n'
    },
    'move_zeroes': {
        "id": 'move_zeroes',
        "title": '5. Move Zeroes',
        "category": 'Two Pointers',
        "code": '# 5. Move Zeroes\n# Shift non-zero elements forward using write/read pointer positions\nnums = [0, 1, 0, 3, 12]\nwrite = 0\n\nfor read in range(len(nums)):\n    if nums[read] != 0:\n        if read != write:\n            nums[write], nums[read] = nums[read], nums[write]\n            print(f"Swapped non-zero {nums[write]} to write={write}")\n        write += 1\n\nprint(f"Array with zeroes moved: {nums}")\n'
    },
    'container_most_water': {
        "id": 'container_most_water',
        "title": '6. Container With Most Water',
        "category": 'Two Pointers',
        "code": '# 6. Container With Most Water\n# Two pointers (left, right) track max water area bounded by shortest height\nheights = [1, 8, 6, 2, 5, 4, 8, 3]\nleft = 0\nright = len(heights) - 1\nmax_area = 0\n\nwhile left < right:\n    h = min(heights[left], heights[right])\n    w = right - left\n    area = h * w\n    if area > max_area:\n        max_area = area\n    print(f"left={left}, right={right}, h={h}, w={w}, area={area}, max={max_area}")\n    if heights[left] < heights[right]:\n        left += 1\n    else:\n        right -= 1\n\nprint(f"Maximum water area: {max_area}")\n'
    },
    'max_sum_subarray': {
        "id": 'max_sum_subarray',
        "title": '7. Maximum Sum Subarray',
        "category": 'Sliding Window',
        "code": '# 7. Maximum Sum Subarray (Fixed Window k = 3)\nnums = [2, 1, 5, 1, 3, 2]\nk = 3\nwindow_sum = sum(nums[:k])\nmax_sum = window_sum\nstart = 0\n\nfor end in range(k, len(nums)):\n    window_sum += nums[end] - nums[start]\n    if window_sum > max_sum:\n        max_sum = window_sum\n    print(f"Window [{start+1}..{end}]: sum={window_sum}, max={max_sum}")\n    start += 1\n\nprint(f"Max window sum: {max_sum}")\n'
    },
    'min_length_subarray': {
        "id": 'min_length_subarray',
        "title": '8. Minimum-Length Subarray',
        "category": 'Sliding Window',
        "code": '# 8. Minimum-Length Subarray Sum >= S\nnums = [2, 3, 1, 2, 4, 3]\ntarget = 7\nstart = 0\ncurr_sum = 0\nmin_len = len(nums) + 1\n\nfor end in range(len(nums)):\n    curr_sum += nums[end]\n    while curr_sum >= target:\n        window_len = end - start + 1\n        if window_len < min_len:\n            min_len = window_len\n        print(f"Valid window [{start}..{end}] sum={curr_sum}, len={window_len}")\n        curr_sum -= nums[start]\n        start += 1\n\nresult = min_len if min_len <= len(nums) else 0\nprint(f"Minimum subarray length for target {target}: {result}")\n'
    },
    'longest_substr_no_repeat': {
        "id": 'longest_substr_no_repeat',
        "title": '9. Longest Substring Without Repeating Characters',
        "category": 'Sliding Window',
        "code": '# 9. Longest Substring Without Repeating Characters\ntext = "abcabcbb"\nchar_index = {}\nstart = 0\nmax_len = 0\nlongest_sub = ""\n\nfor end in range(len(text)):\n    c = text[end]\n    if c in char_index and char_index[c] >= start:\n        start = char_index[c] + 1\n    char_index[c] = end\n    curr_len = end - start + 1\n    if curr_len > max_len:\n        max_len = curr_len\n        longest_sub = text[start:end+1]\n    print(f"end={end}(\'{c}\'), start={start}, window=\'{text[start:end+1]}\', max={max_len}")\n\nprint(f"Longest non-repeating substring: \'{longest_sub}\' (len: {max_len})")\n'
    },
    'fixed_window_average': {
        "id": 'fixed_window_average',
        "title": '10. Fixed-Size Window Average',
        "category": 'Sliding Window',
        "code": '# 10. Fixed-Size Window Average\nreadings = [10, 20, 30, 40, 50, 60]\nk = 3\naverages = []\ncurr_sum = sum(readings[:k])\naverages.append(curr_sum / k)\nstart = 0\n\nfor end in range(k, len(readings)):\n    curr_sum += readings[end] - readings[start]\n    avg = curr_sum / k\n    averages.append(avg)\n    print(f"Window [{start+1}..{end}]: sum={curr_sum}, avg={avg:.2f}")\n    start += 1\n\nprint(f"Moving averages: {averages}")\n'
    },
    'linear_search': {
        "id": 'linear_search',
        "title": '11. Linear Search',
        "category": 'Searching and Arrays',
        "code": '# 11. Linear Search\nnums = [4, 2, 9, 7, 5, 8]\ntarget = 7\nfound_idx = -1\n\nfor i in range(len(nums)):\n    val = nums[i]\n    print(f"Inspecting index i={i}, val={val}")\n    if val == target:\n        found_idx = i\n        print(f"Target {target} located at index {i}")\n        break\n\nprint(f"Linear search result: index {found_idx}")\n'
    },
    'binary_search': {
        "id": 'binary_search',
        "title": '12. Binary Search',
        "category": 'Searching and Arrays',
        "code": '# 12. Binary Search on Sorted Array\nnums = [2, 5, 8, 12, 16, 23, 38, 45, 56, 72]\ntarget = 23\nlow = 0\nhigh = len(nums) - 1\nfound_idx = -1\n\nwhile low <= high:\n    mid = (low + high) // 2\n    print(f"low={low}, high={high}, mid={mid}, nums[mid]={nums[mid]}")\n    if nums[mid] == target:\n        found_idx = mid\n        print(f"Match found at mid={mid}")\n        break\n    elif nums[mid] < target:\n        low = mid + 1\n    else:\n        high = mid - 1\n\nprint(f"Target {target} index: {found_idx}")\n'
    },
    'sentinel_search': {
        "id": 'sentinel_search',
        "title": '13. Sentinel Linear Search',
        "category": 'Searching and Arrays',
        "code": '# 13. Sentinel Linear Search\nvalues = [14, 28, 56, 42, 70]\ntarget = 42\nn = len(values)\nlast = values[-1]\nvalues[-1] = target\ni = 0\n\nwhile values[i] != target:\n    i += 1\n\nvalues[-1] = last\nfound = (i < n - 1) or (last == target)\nprint(f"Target {target} found at index {i}: {found}")\n'
    },
    'prefix_sums': {
        "id": 'prefix_sums',
        "title": '14. Prefix Sums',
        "category": 'Searching and Arrays',
        "code": '# 14. Prefix Sums Array\nnums = [3, 1, 4, 1, 5, 9]\nprefix = [0] * (len(nums) + 1)\n\nfor i in range(len(nums)):\n    prefix[i + 1] = prefix[i] + nums[i]\n    print(f"prefix[{i+1}] = prefix[{i}] + nums[{i}] = {prefix[i+1]}")\n\nprint(f"Original: {nums}")\nprint(f"Prefix sums: {prefix}")\nsub_sum = prefix[4] - prefix[1]\nprint(f"Sum of nums[1..3]: {sub_sum}")\n'
    },
    'frequency_counting': {
        "id": 'frequency_counting',
        "title": '15. Frequency Counting',
        "category": 'Searching and Arrays',
        "code": '# 15. Frequency Counting\nitems = ["apple", "banana", "apple", "cherry", "banana", "apple"]\ncounts = {}\n\nfor idx in range(len(items)):\n    fruit = items[idx]\n    counts[fruit] = counts.get(fruit, 0) + 1\n    print(f"Processed items[{idx}]=\'{fruit}\', count={counts[fruit]}")\n\nprint(f"Final frequencies: {counts}")\n'
    },
    'bubble_sort': {
        "id": 'bubble_sort',
        "title": '16. Bubble Sort',
        "category": 'Sorting',
        "code": '# 16. Bubble Sort\narr = [5, 1, 4, 2, 8]\nn = len(arr)\n\nfor i in range(n):\n    swapped = False\n    for j in range(0, n - i - 1):\n        print(f"Comparing arr[{j}]={arr[j]} and arr[{j+1}]={arr[j+1]}")\n        if arr[j] > arr[j + 1]:\n            arr[j], arr[j + 1] = arr[j + 1], arr[j]\n            swapped = True\n            print(f"  Swapped: {arr}")\n    if not swapped:\n        break\n\nprint(f"Sorted array: {arr}")\n'
    },
    'selection_sort': {
        "id": 'selection_sort',
        "title": '17. Selection Sort',
        "category": 'Sorting',
        "code": '# 17. Selection Sort\narr = [29, 10, 14, 37, 13]\nn = len(arr)\n\nfor i in range(n):\n    min_idx = i\n    for j in range(i + 1, n):\n        if arr[j] < arr[min_idx]:\n            min_idx = j\n    if min_idx != i:\n        arr[i], arr[min_idx] = arr[min_idx], arr[i]\n        print(f"Step {i}: swapped min {arr[i]} into index {i}: {arr}")\n\nprint(f"Sorted array: {arr}")\n'
    },
    'insertion_sort': {
        "id": 'insertion_sort',
        "title": '18. Insertion Sort',
        "category": 'Sorting',
        "code": '# 18. Insertion Sort\narr = [12, 11, 13, 5, 6]\n\nfor i in range(1, len(arr)):\n    key = arr[i]\n    j = i - 1\n    print(f"Inserting key={key} from index i={i}")\n    while j >= 0 and arr[j] > key:\n        arr[j + 1] = arr[j]\n        j -= 1\n    arr[j + 1] = key\n    print(f"  Array after pass {i}: {arr}")\n\nprint(f"Sorted array: {arr}")\n'
    },
    'merge_sort': {
        "id": 'merge_sort',
        "title": '19. Merge Sort',
        "category": 'Sorting',
        "code": '# 19. Iterative Two-Way Merge\nleft_arr = [2, 5, 9]\nright_arr = [1, 4, 8, 10]\nmerged = []\ni = 0\nj = 0\n\nwhile i < len(left_arr) and j < len(right_arr):\n    if left_arr[i] <= right_arr[j]:\n        merged.append(left_arr[i])\n        print(f"Appended left_arr[{i}]={left_arr[i]}")\n        i += 1\n    else:\n        merged.append(right_arr[j])\n        print(f"Appended right_arr[{j}]={right_arr[j]}")\n        j += 1\n\nwhile i < len(left_arr):\n    merged.append(left_arr[i])\n    i += 1\n\nwhile j < len(right_arr):\n    merged.append(right_arr[j])\n    j += 1\n\nprint(f"Merged sorted array: {merged}")\n'
    },
    'matrix_traversal': {
        "id": 'matrix_traversal',
        "title": '20. Nested Matrix Traversal',
        "category": 'Matrices',
        "code": '# 20. Nested Matrix Traversal\nmatrix = [\n    [1, 2, 3],\n    [4, 5, 6]\n]\ntotal = 0\n\nfor i in range(len(matrix)):\n    for j in range(len(matrix[i])):\n        val = matrix[i][j]\n        total += val\n        print(f"matrix[{i}][{j}] = {val}, total = {total}")\n\nprint(f"Matrix sum: {total}")\n'
    },
    'matrix_row_sums': {
        "id": 'matrix_row_sums',
        "title": '21. Row Sums',
        "category": 'Matrices',
        "code": '# 21. Row Sums\ngrid = [\n    [3, 5, 2],\n    [8, 1, 4],\n    [7, 6, 9]\n]\nrow_sums = []\n\nfor i in range(len(grid)):\n    curr_sum = 0\n    for j in range(len(grid[i])):\n        curr_sum += grid[i][j]\n    row_sums.append(curr_sum)\n    print(f"Row {i} sum: {curr_sum}")\n\nprint(f"All row sums: {row_sums}")\n'
    },
    'matrix_col_sums': {
        "id": 'matrix_col_sums',
        "title": '22. Column Sums',
        "category": 'Matrices',
        "code": '# 22. Column Sums\ngrid = [\n    [1, 2, 3],\n    [4, 5, 6],\n    [7, 8, 9]\n]\nnum_cols = len(grid[0])\ncol_sums = [0] * num_cols\n\nfor j in range(num_cols):\n    curr_sum = 0\n    for i in range(len(grid)):\n        curr_sum += grid[i][j]\n    col_sums[j] = curr_sum\n    print(f"Column {j} sum: {curr_sum}")\n\nprint(f"All column sums: {col_sums}")\n'
    },
    'matrix_diagonal': {
        "id": 'matrix_diagonal',
        "title": '23. Diagonal Traversal',
        "category": 'Matrices',
        "code": '# 23. Diagonal Traversal\nsq_matrix = [\n    [1, 2, 3],\n    [4, 5, 6],\n    [7, 8, 9]\n]\nn = len(sq_matrix)\nmain_diag = []\nanti_diag = []\n\nfor i in range(n):\n    main_val = sq_matrix[i][i]\n    anti_val = sq_matrix[i][n - 1 - i]\n    main_diag.append(main_val)\n    anti_diag.append(anti_val)\n    print(f"i={i}: main diag={main_val}, anti diag={anti_val}")\n\nprint(f"Main diagonal: {main_diag}")\nprint(f"Anti diagonal: {anti_diag}")\n'
    },
    'stack_queue_ops': {
        "id": 'stack_queue_ops',
        "title": '24. Stack and Queue Operations',
        "category": 'Stacks, Queues, and Recursion',
        "code": '# 24. Stack and Queue Operations\nstack = []\nqueue = []\n\n# Stack operations (LIFO)\nfor item in [10, 20, 30]:\n    stack.append(item)\n    print(f"Pushed to stack: {item}, current stack={stack}")\n\npopped_stack = stack.pop()\nprint(f"Popped from stack: {popped_stack}, remaining={stack}")\n\n# Queue operations (FIFO)\nfor item in ["alpha", "beta", "gamma"]:\n    queue.append(item)\n    print(f"Enqueued: {item}, queue={queue}")\n\ndequeued = queue.pop(0)\nprint(f"Dequeued: {dequeued}, remaining={queue}")\n'
    },
    'factorial_fibonacci': {
        "id": 'factorial_fibonacci',
        "title": '25. Factorial and Fibonacci Recursion',
        "category": 'Stacks, Queues, and Recursion',
        "code": '# 25. Factorial and Fibonacci Recursion\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\ndef fibonacci(n):\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    return fibonacci(n - 1) + fibonacci(n - 2)\n\nfact_4 = factorial(4)\nprint(f"factorial(4) = {fact_4}")\n\nfib_5 = fibonacci(5)\nprint(f"fibonacci(5) = {fib_5}")\n'
    },
}

ALLOWED_PRESET_IDS = set(ALGORITHM_PRESETS.keys())
