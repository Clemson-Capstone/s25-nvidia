from nemoguardrails import LLMRails, RailsConfig
import os 
import json 
import shutil

def corpus_to_md(path_to_corpus):
    with open(path_to_corpus, "r") as f:
        corpus = json.load(f)

    # Creating a bunch of files inside of kb

    # Remove all .md files in the kb directory (leave the .json file)
    for filename in os.listdir("config/kb"):
        if filename.endswith(".md"):
            os.remove(f"config/kb/{filename}")

    # Write all the chunks as their own .md files
    for key in corpus:
        title = corpus[key]["metadata"]["source_document_name"] + " - " + str(corpus[key]["metadata"]["sequence_number"])
        text = corpus[key]["text"]
        with open(f"config/kb/{title}.md", "w") as f:
            # Write the title
            f.write(f"# {title}\n\n")
            f.write(text)




corpus_to_md("config/kb/corpus.json")

NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
# Load a guardrails configuration from the specified path.
config = RailsConfig.from_path(f"config")
rails = LLMRails(config)

input_test = rails.generate(messages=[{
    "role": "user",
    "content": 'Based on the 1900FA24 Syllabus how many points are possible for the final exam?'
}])
print("Output:\n", input_test["content"], "\n\n")

print(rails.explain())