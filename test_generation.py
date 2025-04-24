from datasets import load_dataset
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

class CodeGenerator:
    def __init__(self):
         # Initializes the CodeGenerator with OpenAI API key.
        load_dotenv(dotenv_path='.env.local')
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            model="gpt-3.5-turbo",
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
            model="gpt-3.5-turbo",
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
    # Test with contraints and without explicitly stating add imports.
    dataset = load_dataset("openai_humaneval")
    problem = dataset['test'][0]
    
    constraints = [
        "Use while loop(s) instead of for loop(s)",
        "Use for loop(s) instead of while loop(s)",
        "Use recursion instead of loop(s)"
    ]
    
    generator = CodeGenerator()
    # Print the problem first before testing
    generator.print_problem_details(problem)
    
    for constraint in constraints:
        print(f"\nTesting constraint: {constraint}")
        generated_code = generator.generate_with_constraint(problem['prompt'], constraint)
        print("\nGenerated Code:")
        print(generated_code)
        
        if run_test(generated_code, problem['test']):
            print("✅ Tests passed!")
        else:
            print("❌ Tests failed!")
            print("Stopping further constraint testing.")
            break

def test_with_constraint_and_import():
     # Test with contraints and with explicitly stating add imports.

    dataset = load_dataset("openai_humaneval")
    problem = dataset['test'][0]
    
    constraints = [
        "Use while loop(s) instead of for loop(s)",
        "Use for loops instead of while loops",
        "Use recursion instead of loops"
    ]
    
    generator = CodeGenerator()

    # Print the problem first before testing
    generator.print_problem_details(problem)
    
    for constraint in constraints:
        print(f"\nTesting constraint with imports: {constraint}")
        generated_code = generator.generate_with_constraint_and_import(problem['prompt'], constraint)
        print("\nGenerated Code:")
        print(generated_code)
        
        if run_test(generated_code, problem['test']):
            print("✅ Tests passed!")
        else:
            print("❌ Tests failed!")
            print("Stopping further constraint testing.")
            break
# Main Function.
if __name__ == "__main__":
    print("Testing without imports...")
    test_with_constraint()
    
    print("\nTesting with imports...")
    test_with_constraint_and_import()