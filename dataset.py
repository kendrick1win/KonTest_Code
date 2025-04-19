
from datasets import load_dataset
import random




def prepare_humaneval_dataset(num_programs=20):
    """Select and prepare programs from HumanEval"""
    dataset = load_dataset("openai_humaneval")
    
    # Select a diverse set of programs
    selected_programs = []
    for problem in random.sample(list(dataset['test']), num_programs):
        selected_programs.append({
            'id': problem['task_id'],
            'prompt': problem['prompt'],
            'completion': problem['canonical_solution'],
            'test': problem['test']
        })
    print(selected_programs)
    return selected_programs

prepare_humaneval_dataset(1)