from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from datetime import datetime

def load_text_file(file_path):
    """Load text content from a file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def calculate_semantic_similarity(text1, text2, model):
    """Calculate semantic similarity between two texts"""
    embeddings = model.encode([text1, text2])
    return cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

def calculate_keyword_overlap(query, response):
    """Calculate percentage of query keywords found in response"""
    query_words = set(query.lower().split())
    response_words = set(response.lower().split())
    common_words = query_words.intersection(response_words)
    return len(common_words) / len(query_words) if len(query_words) > 0 else 0

def evaluate_response_quality(response):
    """Evaluate response against quality heuristics"""
    response_lower = response.lower()
    return {
        "does_not_contain_answer": not any(word in response_lower for word in ["the answer", "the solution"]),
        "ends_properly": response.strip().endswith(('.', '?', '!')),
        "avoids_opinion": not any(word in response_lower for word in ["i think", "in my opinion", "best"])
    }

def generate_report(results, output_path=None):
    """Generate formatted evaluation report"""
    report_lines = []
    report_lines.append("\n" + "="*40)
    report_lines.append("COMPREHENSIVE EVALUATION REPORT")
    report_lines.append("="*40)
    
    for key, value in results.items():
        if key == 'quality_metrics':
            report_lines.append("\nQuality Heuristics:")
            for metric, val in value.items():
                report_lines.append(f"- {metric.replace('_', ' ').title()}: {'✓' if val else '✗'}")
        else:
            if isinstance(value, float):
                report_lines.append(f"- {key.replace('_', ' ').title()}: {value:.2f}")
            else:
                report_lines.append(f"- {key.replace('_', ' ').title()}: {value}")

    report_text = "\n".join(report_lines)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    return report_text

def process_pair(query_path, response_path, model, eval_dir):
    """Process a single query-response pair"""
    try:
        user_query = load_text_file(query_path)
        llm_response = load_text_file(response_path)
    except Exception as e:
        print(f"Error loading files: {e}")
        print(f"Query path: {query_path}")
        print(f"Response path: {response_path}")
        return None

    semantic_sim = calculate_semantic_similarity(user_query, llm_response, model)
    
    query_words = user_query.split()
    response_words = llm_response.split()
    length_ratio = len(response_words) / len(query_words) if query_words else 0
    
    keyword_overlap = calculate_keyword_overlap(user_query, llm_response)
    quality_metrics = evaluate_response_quality(llm_response)

    overall_score = (
        0.4 * semantic_sim +
        0.2 * min(length_ratio, 3)/3 + 
        0.2 * keyword_overlap +
        0.2 * (sum(quality_metrics.values())/len(quality_metrics))
    )

    results = {
        "semantic_similarity": semantic_sim,
        "query_length": len(query_words),
        "response_length": len(response_words),
        "length_ratio": length_ratio,
        "keyword_overlap": keyword_overlap,
        "quality_metrics": quality_metrics,
        "overall_score": overall_score
    }

    # Create evaluation filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_filename = f"eval_{Path(query_path).stem}_{timestamp}.txt"
    eval_path = os.path.join(eval_dir, eval_filename)
    
    # Generate and save report
    report = generate_report(results, eval_path)
    
    print(f"\nProcessed: {Path(query_path).name}")
    print(f"Evaluation saved to: {eval_path}")
    
    if overall_score < 0.5:
        print("WARNING: Low overall score detected")
    
    return results

def main():
    # Initialize model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Configure paths
    base_dir = Path(r"C:\Users\jayle\s25-nvidia\benchmarks\data")
    queries_dir = base_dir / "queries"
    responses_dir = base_dir / "responses"
    evaluations_dir = base_dir / "evaluations"
    
    # Create evaluations directory if it doesn't exist
    evaluations_dir.mkdir(exist_ok=True)
    
    # Get all query files
    query_files = list(queries_dir.glob("*.txt"))
    
    if not query_files:
        print(f"No query files found in {queries_dir}")
        return
    
    # Process each query-response pair
    for query_path in query_files:
        # Find matching response file
        response_filename = query_path.name.replace("user_query", "vta_response")
        response_path = responses_dir / response_filename
        
        if not response_path.exists():
            print(f"\nNo matching response found for {query_path.name}")
            continue
            
        process_pair(query_path, response_path, model, evaluations_dir)

if __name__ == "__main__":
    main()