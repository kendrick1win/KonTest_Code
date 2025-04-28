from datasets import load_dataset
import os
from dotenv import load_dotenv
from groq import Groq 
import re

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

    def generate_with_constraint(self, prompt: str, constraint: str) -> str:
        full_prompt = f"Write Python code following this constraint: {constraint} if possible else state not possible. Task: {prompt}"
        response = self.client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # Update model
            messages=[
                {
                    "role": "system",
                    "content": "You are a code generator. Return only the function implementation without markdown code blocks."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        )
        return response.choices[0].message.content
        
    def generate_with_constraint_and_import(self, prompt: str, constraint: str) -> str:
        full_prompt = f"""Write Python code following this constraint: {constraint}. 
        Include all necessary imports at the top of your code. Task: {prompt}"""
        response = self.client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # Update model
            messages=[
                {
                    "role": "system",
                    "content": "You are a code generator. Return only the function implementation without markdown code blocks."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        )
        return response.choices[0].message.content

def extract_code(generated_code: str) -> str:
    code = re.sub(r'```python\n', '', generated_code)
    code = re.sub(r'```', '', code)
    return code.strip()

def run_test(generated_code: str, test_code: str) -> bool:
    # Run test using HumanEval
    try:
        namespace = {}
        exec(extract_code(generated_code), namespace)
        exec(test_code, namespace)
        return True
    except AssertionError:
        return False
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        return False


def test_with_constraint():
    dataset = load_dataset("openai_humaneval")
    generator = CodeGenerator()
    
    constraints = [
        "Use while loop(s) instead of for loop(s)",
        "Use for loop(s) instead of while loop(s)",
        "Use recursion instead of loop(s)"
    ]
    
    results = {constraint: {'passed': 0, 'failed': 0} for constraint in constraints}
    
    for i, problem in enumerate(dataset['test']):
        print(f"\n\nTesting Problem {i+1}/{len(dataset['test'])}")
        generator.print_problem_details(problem)
        
        for constraint in constraints:
            print(f"\nTesting constraint: {constraint}")
            generated_code = generator.generate_with_constraint(problem['prompt'], constraint)
            print("\nGenerated Code:")
            print(generated_code)
            
            if run_test(generated_code, problem['test']):
                print("✅ Tests passed!")
                results[constraint]['passed'] += 1
            else:
                print("❌ Tests failed!")
                results[constraint]['failed'] += 1
    
    # Print summary
    print("\n=== FINAL RESULTS ===")
    for constraint, scores in results.items():
        total = scores['passed'] + scores['failed']
        success_rate = (scores['passed'] / total) * 100 if total > 0 else 0
        print(f"\n{constraint}:")
        print(f"Passed: {scores['passed']}")
        print(f"Failed: {scores['failed']}")
        print(f"Success Rate: {success_rate:.2f}%")

def test_with_constraint_and_import():
    dataset = load_dataset("openai_humaneval")
    generator = CodeGenerator()
    
    constraints = [
        "Use while loop(s) instead of for loop(s)",
        "Use for loops instead of while loops",
        "Use recursion instead of loops"
    ]
    
    results = {constraint: {'passed': 0, 'failed': 0} for constraint in constraints}
    
    # Limit to first 5 problems
    for i, problem in enumerate(list(dataset['test'])[:5]):
        print(f"\n\nTesting Problem {i+1}/5")  # Updated to show 5 instead of total length
        generator.print_problem_details(problem)
        
        for constraint in constraints:
            print(f"\nTesting constraint with imports: {constraint}")
            generated_code = generator.generate_with_constraint_and_import(problem['prompt'], constraint)
            print("\nGenerated Code:")
            print(generated_code)
            
            if run_test(generated_code, problem['test']):
                print("✅ Tests passed!")
                results[constraint]['passed'] += 1
            else:
                print("❌ Tests failed!")
                results[constraint]['failed'] += 1
    
    # Print summary
    print("\n=== FINAL RESULTS ===")
    for constraint, scores in results.items():
        total = scores['passed'] + scores['failed']
        success_rate = (scores['passed'] / total) * 100 if total > 0 else 0
        print(f"\n{constraint}:")
        print(f"Passed: {scores['passed']}")
        print(f"Failed: {scores['failed']}")
        print(f"Success Rate: {success_rate:.2f}%")

if __name__ == "__main__":
    print("Testing without imports...")
    #test_with_constraint()
    
    print("\nTesting with imports...")
    test_with_constraint_and_import()
