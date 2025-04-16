from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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
        "contains_reasoning": any(word in response_lower for word in ["because", "therefore", "thus"]),
        "is_structured": any(word in response_lower for word in ["first", "second", "finally"]),
        "ends_properly": response.strip().endswith(('.', '?', '!')),
        "avoids_opinion": not any(word in response_lower for word in ["i think", "in my opinion", "best"])
    }

def generate_report(results):
    """Generate formatted evaluation report"""
    print("\n" + "="*40)
    print("COMPREHENSIVE EVALUATION REPORT")
    print("="*40)
    
    for key, value in results.items():
        if key == 'quality_metrics':
            print("\nQuality Heuristics:")
            for metric, val in value.items():
                print(f"- {metric.replace('_', ' ').title()}: {'✓' if val else '✗'}")
        else:
            if isinstance(value, float):
                print(f"- {key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"- {key.replace('_', ' ').title()}: {value}")

def main():
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    query_path = r"C:\Users\jayle\s25-nvidia\benchmarks\data\queries\user_query_20250403_202616_074332.txt"
    response_path = r"C:\Users\jayle\s25-nvidia\benchmarks\data\responses\vta_response_20250403_202616_074332.txt"

    try:
        user_query = load_text_file(query_path)
        llm_response = load_text_file(response_path)
    except Exception as e:
        print(f"Error loading files: {e}")
        print(f"Query path: {query_path}")
        print(f"Response path: {response_path}")
        return

    print("=== USER QUERY ===\n", user_query)
    print("\n=== LLM RESPONSE ===\n", llm_response)

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

    generate_report(results)

    if overall_score < 0.5:
        print("\nWARNING: Low overall score detected. Key issues:")
        if semantic_sim < 0.3:
            print("- Response doesn't address the query's core meaning")
        if length_ratio > 5:
            print("- Response may be too verbose")
        if keyword_overlap < 0.2:
            print("- Important keywords from query are missing")

if __name__ == "__main__":
    main()