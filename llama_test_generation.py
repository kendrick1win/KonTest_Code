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
    code = re.sub(r'```python\n', '', generated_code)
    code = re.sub(r'```', '', code)
    return code.strip()

def run_test(generated_code: str, test_code: str) -> tuple[bool, bool]:
    if "# API Error:" in generated_code:
        return False, True

    try:
        namespace = {}

        # Extract and execute generated solution
        exec(extract_code(generated_code), namespace)

        # Ensure 'solution' exists
        if 'has_close_elements' not in namespace or not callable(namespace['has_close_elements']):
            print("No valid 'has_close_elements' function defined.")
            return False, False

        # Add alias for expected name in test code
        namespace['candidate'] = namespace['has_close_elements']

        # Execute test code which uses 'check(candidate)'
        exec(test_code, namespace)

        return True, False
    except AssertionError as ae:
        print(f"AssertionError: {ae}")
        return False, False
    except Exception as e:
        print(f"Execution Error: {e}")
        return False, False



def test_with_constraint_and_import():
    logger = OutputLogger('test_results.txt')
    dataset = load_dataset("openai_humaneval")
    generator = CodeGenerator()
    
    constraints = [
        "Use while loop(s) instead of for loop(s)",
        "Use for loops instead of while loops",
        "Use recursion instead of loops"
    ]
    
    # Add failed_problems tracking to results dictionary
    results = {constraint: {
        'passed': 0, 
        'failed': 0, 
        'api_errors': 0,
        'failed_problems': []  # Track failed problem IDs
    } for constraint in constraints}
    total_tests = 0
    
    # Problems limit
    for i, problem in enumerate(list(dataset['test'])[:1]):
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
            logger.log("\nGenerated Code:")
            logger.log(generated_code)
            
            is_success, is_api_error = run_test(generated_code, problem['test'])
            if is_api_error:
                logger.log("⚠️ API Error encountered!")
                results[constraint]['api_errors'] += 1
                results[constraint]['failed_problems'].append(f"Problem {i+1} (Task ID: {problem['task_id']}) - API Error")
            elif is_success:
                logger.log("✅ Tests passed!")
                results[constraint]['passed'] += 1
            else:
                logger.log("❌ Tests failed!")
                results[constraint]['failed'] += 1
                results[constraint]['failed_problems'].append(f"Problem {i+1} (Task ID: {problem['task_id']})")
            
            # Display running totals after each test
            logger.log("\n--- Current Results ---")
            logger.log(f"Total tests run: {total_tests}")
            for c, scores in results.items():
                total = scores['passed'] + scores['failed']
                rate = (scores['passed'] / total) * 100 if total > 0 else 0
                logger.log(f"\n{c}:")
                logger.log(f"Passed: {scores['passed']} | Failed: {scores['failed']} | API Errors: {scores['api_errors']}")
                logger.log(f"Current Success Rate: {rate:.2f}%")
                if scores['failed_problems']:
                    logger.log("Failed Problems:")
                    for prob in scores['failed_problems']:
                        logger.log(f"- {prob}")
            logger.log("=" * 50)

    # Print final summary
    logger.log("\n=== FINAL RESULTS ===")
    for constraint, scores in results.items():
        total = scores['passed'] + scores['failed']
        success_rate = (scores['passed'] / total) * 100 if total > 0 else 0
        logger.log(f"\n{constraint}:")
        logger.log(f"Passed: {scores['passed']}")
        logger.log(f"Failed: {scores['failed']}")
        logger.log(f"API Errors: {scores['api_errors']}")
        logger.log(f"Final Success Rate: {success_rate:.2f}%")
        if scores['failed_problems']:
            logger.log("\nFailed Problems:")
            for prob in scores['failed_problems']:
                logger.log(f"- {prob}")
    
    logger.close()

if __name__ == "__main__":

    
    print("\nTesting with imports...")
    test_with_constraint_and_import()
