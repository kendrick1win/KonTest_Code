def solve(N):
    binary_sum = 0
    while N > 0:
        binary_sum += N % 2
        N //= 2
    result = ""
    while binary_sum > 0:
        result = str(binary_sum % 2) + result
        binary_sum //= 2
    return result if result else "0"

test_cases = [
    (1000, "1"),
    (150, "110"),
    (147, "1100"),
    (333, "1001"),
    (963, "10010"),
]

for N, expected in test_cases:
    result = solve(N)
    print(f"N = {N}, solve(N) = {result}, expected = {expected}, PASS = {result == expected}")
