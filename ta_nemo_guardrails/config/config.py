# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.llms import BaseLLM
from langchain_core.output_parsers import StrOutputParser

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.kb.kb import KnowledgeBase
# from beir_kb import BEIRKnowledgeBase
from typing import List
from nemoguardrails.embeddings.providers.base import EmbeddingModel

from nemoguardrails.server.api import register_datastore
from nemoguardrails.server.datastore.memory_store import MemoryStore
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain_core.language_models.llms import BaseLLM

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult

register_datastore(MemoryStore())
import numpy as np
from langchain.chains.combine_documents import create_stuff_documents_chain

from typing import Optional

import os
import faiss
import pickle
import json

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
import faiss.contrib.torch_utils

from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.documents import Document



def _make_bm25_retriever(data_path):
    # Load the corpus from JSON and create BM25Retriever
    corpus = json.load(open(data_path))
    documents = [
        Document(page_content=block["text"], metadata={"source_document_name": block["metadata"]['source_document_name']})
        for doc_id, block in corpus.items()
    ]
    retriever = BM25Retriever.from_documents(documents)
    return retriever



def _make_faiss_gpu(data_path, out_path, embeddings):
    # Here we process the txt files under the data_path folder.

    docs = []
    metadatas = []

    corpus = json.load(open(data_path))
    for doc in corpus:
        block = corpus[doc]
        sdn = block["metadata"]["source_document_name"]
        docs.append(sdn + ": " + block["text"])
        metadatas.append({"source": sdn})

    # Here we create a vector store from the documents and save it to disk.
    store = FAISS.from_texts(docs, embeddings, metadatas=metadatas)
    os.makedirs(out_path, exist_ok=True)
    # faiss.write_index(store.index, out_path + "docs.index")
    # store.index = None
    # with open(out_path + "faiss_store.pkl", "wb") as f:
    #     pickle.dump(store, f)

    store.save_local(out_path)
    return store



def _get_vector_db(data_path: str, persist_path: str):
    """Creates a vector DB for a given data path.

    data_path: path to the corpus.json
    """



    ##set up the nvidia Langchain embedding model
    # embedder = NVIDIAEmbeddings(base_url="http://localhost:8080/v1")
    # embedder = NVIDIAEmbeddings("snowflake/arctic-embed-l")
    embedder = OpenAIEmbeddings(max_retries=2)

    using_vectorstore = "faiss"
    if using_vectorstore == "faiss":
        if os.path.exists(persist_path) and os.path.exists(os.path.join(persist_path, "docs.index")):
            # index = faiss.read_index(os.path.join(persist_path, "docs.index"))
            # with open(os.path.join(persist_path, "faiss_store.pkl"), "rb") as f:
            #     vectordb = pickle.load(f)
            # vectordb.index = index
            vectordb = FAISS.load_local(persist_path, embedder)
        else:
            data_path = data_path
            vectordb = _make_faiss_gpu(data_path, persist_path, embedder)
    return vectordb

vectordb = None


# def init_vectordb_model(config: RailsConfig, context:Optional[dict] = None,):
#     global vectordb

#     # user_id = context.get("user_id")
#     # course_id = context.get("course_id")
#     user_id = "0d81115a7a21748504bbde591e39ba79ef4877afbfed94bf574bc8e8fb7ab152"
#     course_id = "239960"

#     df = f"/project/crusse4/nvidia_f24/course_data/{user_id}/{course_id}"
#     df += f"/{os.listdir(df)[0]}/corpus.json"

#     vectordb = _get_vector_db(
#         data_path=df,
#         persist_path= f"/project/crusse4/nvidia_f24/vd/{user_id}/{course_id}",
#     )

def init_vectordb_model_with_hybrid(config: RailsConfig, context: Optional[dict] = None):
    global vectordb, bm25_retriever, ensemble_retriever

    user_id = "0a3633d13f97ec88f78f0f03a133a4d7574be245fd78cf592c79722952463356"
    course_id = "237571"

    # Define the paths for the data and vector stores
    df = f"/project/crusse4/nvidia_f24/course_data/{user_id}/{course_id}"
    df += f"/{os.listdir(df)[0]}/corpus.json"

    # Initialize FAISS vector store
    vectordb = _get_vector_db(data_path=df, persist_path=f"/project/crusse4/nvidia_f24/vd/{user_id}/{course_id}")

    # Initialize BM25 retriever
    bm25_retriever = _make_bm25_retriever(df)

    # Combine BM25 and FAISS into an ensemble retriever
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vectordb.as_retriever(search_type="similarity")],
        weights=[0.4, 0.6],  # Adjust weights based on your use case
    )


TEMPLATE = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know; don't try to make up an answer.
Use three sentences maximum and keep the answer as concise as possible.

{context}

Question: {question}

Helpful Answer:"""

@action(is_system_action=True)
async def retrieve_relevant_chunks(
    context: dict,
    llm: BaseLLM
):
    """Retrieve relevant chunks from the knowledge base and add them to the context."""

    user_message = context.get("last_user_message")

    # # If the user id or course id is not in the context, return an error
    # if "user_id" not in context or "course_id" not in context or not context['user_id'] or not context['course_id']:
    #     return ActionResult(
    #         return_value="Error: No course has been loaded for RAG"
    #     )

    # init_vectordb_model(None, context)

    init_vectordb_model_with_hybrid(None, context)

    # Retrieve relevant documents using the hybrid ensemble retriever
    docs = ensemble_retriever.invoke(user_message)
    
    print("Docs: ", docs)
    # Set up the retriever to get multiple documents
    # retriever = vectordb.as_retriever(
    #     search_type="similarity", search_kwargs={"k": 10}
    # )

    # # Retrieve the documents
    # docs = retriever.get_relevant_documents(user_message)

    # Load a QA chain that can handle multiple documents
    from langchain.chains.question_answering import load_qa_chain
    chain = load_qa_chain(llm, chain_type='stuff')

    # Run the chain with the documents and question
    out = chain({
        "input_documents": docs,
        "question": user_message
    })

    # Extract the answer and sources
    result = out['output_text']
    citing_texts = [doc.page_content for doc in docs]
    source_refs = [doc.metadata.get('source', '') for doc in docs]

    context_updates = {
        "relevant_chunks": f"""
        Question: {user_message}
        Answer: {result}
        Citing Texts: {citing_texts}
        Source References: {source_refs}
        """
    }

    return ActionResult(
        return_value=result + "<br><br> Sources:<br>\n" + "<br>".join(source_refs) + "<br><br>Citing Texts:<br>" + "<br><br>".join(citing_texts),
        context_updates=context_updates,
    )











TEMPLATE = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use three sentences maximum and keep the answer as concise as possible.

{context}

Question: {question}

Helpful Answer:"""

async def rag(context: dict, llm: BaseLLM, kb: KnowledgeBase) -> ActionResult:
    MAX_CONTEXT_CHARS = 8192

    #print the context
    print("Context: ", context)

    user_message = context.get("last_user_message")
    user_id = context.get("user_id")
    course_id = context.get("course_id")
    context_updates = {}

    # For our custom RAG, we re-use the built-in retrieval
    chunks = await kb.search_relevant_chunks(user_message, max_results=12)

    print("Number of chunks chosen: ", len(chunks))
    print("Amount of characters in each chunk: ", [len(chunk["body"]) for chunk in chunks])
    print("Chunks chosen: ", [chunk['title'] for chunk in chunks])
    # print("chunk 0", chunks[0])
    # exit(1)

    counted_chars = 0
    kept_chunks = []
    for chunk in chunks:
        counted_chars += len(chunk["body"])
        if counted_chars > MAX_CONTEXT_CHARS:
            break
        kept_chunks.append(chunk)

    chunks = kept_chunks
    print("Chunks kept: ", [chunk['title'] for chunk in chunks])


    relevant_chunks = "\n".join([chunk["body"] for chunk in chunks])
    # 💡 Store the chunks for fact-checking
    context_updates["relevant_chunks"] = relevant_chunks

    # Use a custom prompt template
    prompt_template = PromptTemplate.from_template(TEMPLATE)
    input_variables = {"question": user_message, "context": relevant_chunks}
    # 💡 Store the template for hallucination-checking
    context_updates["_last_bot_prompt"] = prompt_template.format(**input_variables)

    # print(f"💬 RAG :: prompt_template: {context_updates['_last_bot_prompt']}")

    # Put together a simple LangChain chain
    output_parser = StrOutputParser()
    chain = prompt_template | llm | output_parser
    answer = await chain.ainvoke(input_variables)

    # Extract titles of the chunks
    titles = [chunk["title"] for chunk in chunks]
    titles_str = ", ".join(titles)

    # Append titles to the answer
    final_answer = f"{answer}\n\nSources:\n{titles_str}\n\nUser ID: {user_id}\nCourse ID: {course_id}"

    return ActionResult(return_value=final_answer, context_updates=context_updates)





quiz_response_template = """
Based on the following quiz question a student asked, do not answer the question directly.
Instead, provide a response that is helpful to the student in answering the question and explains the underlying concepts.

Question: {question}

Concept Explanation (no answer):


"""

async def quiz_reponse(context: dict, llm: BaseLLM):
    inputs = context.get("last_user_message")
    output_parser = StrOutputParser()
    prompt_template = PromptTemplate.from_template(quiz_response_template)
    input_variables = {"question": inputs}
    chain = prompt_template | llm | output_parser
    answer = await chain.ainvoke(input_variables)
    return answer

# Template where the chatbot will not say exactly what the problem with their code
# is, but present ideas to the user to help them debug their code and hints
code_debug_response_template = """
Based on the code snippet provided, do not provide the exact solution to debug the code.
Instead, provide ideas and hints to help the user debug the code.
Bring up relevant concepts and ask questions to guide the user in debugging their code.

Code Snippet:
{code}

Debugging Hints and concept explanations:

"""
async def code_debug_response(context: dict, llm: BaseLLM):
    inputs = context.get("last_user_message")
    output_parser = StrOutputParser()
    prompt_template = PromptTemplate.from_template(code_debug_response_template)
    input_variables = {"code": inputs}
    chain = prompt_template | llm | output_parser
    answer = await chain.ainvoke(input_variables)
    return answer + " (code debug response)"

def init(app: LLMRails):
    # app.register_action(rag, "rag")
    app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")
    app.register_action(code_debug_response, "code_debug_response")
    app.register_action(quiz_reponse, "quiz_response")
