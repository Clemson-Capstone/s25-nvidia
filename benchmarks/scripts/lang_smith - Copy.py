import json
from langsmith import Client
from langchain_community.llms import Ollama 
from typing import Dict, Any
import os

os.environ["LANGCHAIN_API_KEY"] = "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"
client = Client()

class FreeVTALEvaluator:
    def __init__(self):
        """Initialize with free local LLMs"""
        self.evaluator_llm = Ollama(
            model="mistral", 
            temperature=0.2,
            num_ctx=2048
        )
        self.quality_llm = Ollama(
            model="llama3",
            temperature=0.3,
            num_ctx=4096
        )

    def load_files(self, questions_path: str, responses_path: str) -> list:
        """Load dataset from text files"""
        def read_lines(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return [line.strip() for line in f if line.strip()]
            except Exception as e:
                print(f"Error reading {path}: {str(e)}")
                return []
        
        questions = read_lines(questions_path)
        responses = read_lines(responses_path)
        min_len = min(len(questions), len(responses))
        return [
            {"user_input": q, "vta_response": r}
            for q, r in zip(questions[:min_len], responses[:min_len])
        ]

    def evaluate_response(self, user_input: str, response: str) -> Dict[str, Any]:
        """Evaluate a single response"""
        try:
         
            if any(word in response.lower() for word in ["harmful", "dangerous"]):
                return {"score": 0, "reason": "Safety violation"}
                
            if "?" in response and "solution" not in response.lower():
                return {"score": 0.8, "reason": "Good questioning approach"}
      
            prompt = f"""Rate this teaching response (0-1):
            Question: {user_input}
            Response: {response}
            
            Consider:
            - Accuracy (0-1)
            - Helpfulness (0-1)
            - Safety (0-1)
            
            Return JSON: {{"score": float, "reason": str}}"""
            
            result = self.evaluator_llm.invoke(prompt)
            return json.loads(result.strip())
            
        except Exception as e:
            return {"score": 0.5, "reason": f"Evaluation error: {str(e)}"}

def main():
    evaluator = FreeVTALEvaluator()
    
    QUESTIONS_PATH = "benchmarks/data/queries/user_query_20250324_183858_364764.txt"
    RESPONSES_PATH = "benchmarks/data/responses/vta_response_20250324_180839_213040.txt"

    dataset = evaluator.load_files(QUESTIONS_PATH, RESPONSES_PATH)
    if not dataset:
        print("Error: Could not load dataset")
        return


    results = []
    for item in dataset:
        results.append(evaluator.evaluate_response(
            item["user_input"],
            item["vta_response"]
        ))
    EVALUATION_DIR = "benchmarks/data/evaluations"
    os.makedirs(EVALUATION_DIR, exist_ok=True) 
    RESULTS_PATH = os.path.join(EVALUATION_DIR, "evaluation_results.json")
    with open(RESULTS_PATH, 'w') as f:
        json.dump({
            "average_score": sum(r["score"] for r in results) / len(results),
            "detailed_results": results
        }, f, indent=2)
    
    print("Evaluation complete! Results saved to evaluation_results.json")

if __name__ == "__main__":
    main()