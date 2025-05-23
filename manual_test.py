from datasets import load_dataset

def run_humaneval_test(problem_id: int, generated_code: str):
    # Load HumanEval dataset
    dataset = load_dataset("openai_humaneval", split="test")

    # Get the selected problem
    problem = dataset[problem_id]
    test_code = problem["test"]

    namespace = {}
    try:
        # Run the generated code (injects your solution into namespace)
        exec(generated_code, namespace)

        # Automatically find the function name from the prompt
        # E.g., "def has_close_elements(...):"
        match = next((line for line in generated_code.splitlines() if line.strip().startswith("def ")), None)
        if not match:
            raise Exception("No function definition found.")

        func_name = match.split("def ")[1].split("(")[0].strip()
        namespace["candidate"] = namespace[func_name]  # Alias for test

        # Run the HumanEval check(candidate)
        exec(test_code, namespace)

        # All asserts passed
        print(f"✅ Problem {problem_id}: All tests passed!")

    except AssertionError as ae:
        print(f"❌ Problem {problem_id}: Test failed - {ae}")
    except Exception as e:
        print(f"❌ Problem {problem_id}: Error - {e}")


# Example usage:
generated_code = """
from typing import List

def has_close_elements(numbers: List[float], threshold: float) -> bool:
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if abs(numbers[i] - numbers[j]) < threshold:
                return True
    return False
"""

if __name__ == "__main__":
    run_humaneval_test(0, generated_code)
