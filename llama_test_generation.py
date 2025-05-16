from datasets import load_dataset
import os
from dotenv import load_dotenv
from groq import Groq 
import re
from output_logger import OutputLogger

class CodeGenerator:
    def __init__(self):
        # Initializes the CodeGenerator with Groq API key
        load_dotenv(dotenv_path='.env.local')
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))  # Change to GROQ_API_KEY

    def print_problem_details(self, problem):
        print("\n=== PROBLEM DETAILS ===")
        print("Task ID:", problem['task_id'])
        print("\nPROMPT:")
        print(problem['prompt'])
        print("\nCANONICAL SOLUTION:")
        print(problem['canonical_solution'])
        print("\nTEST CASES:")
        print(problem['test'])
        print("=" * 50) # prints seperator.

        
    def generate_with_constraint_and_import(self, prompt: str, constraint: str) -> str:
        try:
            full_prompt = f"""Write Python code following this constraint: {constraint}. 
            Include all necessary imports at the top of your code. Task: {prompt}"""
            response = self.client.chat.completions.create(
                # Use a more stable model
                model="meta-llama/llama-4-scout-17b-16e-instruct",  
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code generator. Return only the function implementation without markdown code blocks."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            print(error_msg)
            return f"# {error_msg}\n# Returning empty function as fallback\ndef solution():\n    pass"


def extract_code(generated_code: str) -> str:
    """
    Cleans the generated code by:
    - Removing markdown formatting like ```python
    - Stripping out unsafe or noisy lines like sys.exit(), exit(), and top-level print()
    Returns raw executable Python code.
    """
    # Remove triple backticks and language hints
    code = re.sub(r"```(?:python)?\s*", "", generated_code, flags=re.IGNORECASE)
    code = re.sub(r"```", "", code)

    # Split lines and filter out dangerous or noisy lines
    lines = code.strip().splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Filter out common undesired lines
        if (
            stripped.startswith("print(") or
            stripped.startswith("sys.exit()") or
            stripped.startswith("exit()") or
            stripped == "pass"  # Optional: to remove placeholder bodies
        ):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def test_with_constraint_and_import():
    logger = OutputLogger('test_results.txt')
    dataset = load_dataset("openai_humaneval")
    generator = CodeGenerator()
    
    constraints = [
        "Use while loop(s) instead of for loop(s)",
        "Use for loops instead of while loops",
        "Use recursion instead of loops"
    ]
    
    # Results tracking
    results = {
        constraint: {
            'passed': 0,
            'failed': 0,
            'failed_problems': []
        } for constraint in constraints
    }
    
    total_tests = 0
    
    for i, problem in enumerate(list(dataset['test'])[102:]):
        logger.log(f"\n\nTesting Problem {i+1}")
        logger.log("\n=== PROBLEM DETAILS ===")
        logger.log(f"Task ID: {problem['task_id']}")
        logger.log(f"\nPROMPT:\n{problem['prompt']}")
        logger.log(f"\nCANONICAL SOLUTION:\n{problem['canonical_solution']}")
        logger.log(f"\nTEST CASES:\n{problem['test']}")
        logger.log("=" * 50)
        
        for constraint in constraints:
            total_tests += 1
            logger.log(f"\nTesting constraint with imports: {constraint}")
            generated_code = generator.generate_with_constraint_and_import(problem['prompt'], constraint)
            extracted_code = extract_code(generated_code)
            logger.log("\nGenerated Code:")
            logger.log(extracted_code)
            
            is_success = run_humaneval_test(problem, extracted_code, logger)

            if is_success:
                logger.log("✅ Tests passed!")
                results[constraint]['passed'] += 1
            else:
                logger.log("❌ Tests failed!")
                results[constraint]['failed'] += 1
                results[constraint]['failed_problems'].append(f"Problem {i+1} (Task ID: {problem['task_id']})")

            # Live result log
            logger.log("\n--- Current Results ---")
            logger.log(f"Total tests run: {total_tests}")
            for c, scores in results.items():
                total = scores['passed'] + scores['failed']
                rate = (scores['passed'] / total) * 100 if total > 0 else 0
                logger.log(f"\n{c}:")
                logger.log(f"Passed: {scores['passed']} | Failed: {scores['failed']}")
                logger.log(f"Current Success Rate: {rate:.2f}%")
                if scores['failed_problems']:
                    logger.log("Failed Problems:")
                    for prob in scores['failed_problems']:
                        logger.log(f"- {prob}")
            logger.log("=" * 50)
    # Final Summary
    logger.log("\n=== FINAL RESULTS ===")
    for constraint, scores in results.items():
        total = scores['passed'] + scores['failed']
        success_rate = (scores['passed'] / total) * 100 if total > 0 else 0
        logger.log(f"\n{constraint}:")
        logger.log(f"Passed: {scores['passed']}")
        logger.log(f"Failed: {scores['failed']}")
        logger.log(f"Final Success Rate: {success_rate:.2f}%")
        if scores['failed_problems']:
            logger.log("Failed Problems:")
            for prob in scores['failed_problems']:
                logger.log(f"- {prob}")
    
    logger.close()


def run_humaneval_test(problem, generated_code: str, logger: OutputLogger) -> bool:
    namespace = {}
    try:
        exec(generated_code, namespace)

        # Automatically extract the function name
        match = next((line for line in generated_code.splitlines() if line.strip().startswith("def ")), None)
        if not match:
            raise Exception("No function definition found.")

        func_name = match.split("def ")[1].split("(")[0].strip()
        if func_name not in namespace:
            raise Exception(f"Function '{func_name}' not found.")

        # Alias for HumanEval check()
        namespace["candidate"] = namespace[func_name]

        # Run official test code from HumanEval
        exec(problem["test"], namespace)

        return True  # All tests passed

    except AssertionError as ae:
        logger.log(f"❌ Test failed for Task ID: {problem['task_id']}")
        logger.log(f"AssertionError: {ae}")
        return False
    except Exception as e:
        logger.log(f"❌ Execution error for Task ID: {problem['task_id']}")
        logger.log(f"Exception: {e}")
        return False
    

if __name__ == "__main__":

    
    print("\nTesting with imports...")
    test_with_constraint_and_import()
