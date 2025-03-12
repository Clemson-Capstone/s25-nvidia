# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import logging
import os
from traceback import print_exc
from typing import Any
from typing import Dict
from typing import Generator
from typing import List

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableAssign
from langchain_core.runnables import RunnablePassthrough
from requests import ConnectTimeout
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from langchain.prompts import PromptTemplate
from langchain_core.language_models.llms import BaseLLM

from .base import BaseExample

from .server import Message
from .utils import create_vectorstore_langchain
from .utils import del_docs_vectorstore_langchain
from .utils import get_config
from .utils import get_docs_vectorstore_langchain
from .utils import get_embedding_model
from .utils import get_llm
from .utils import get_prompts
from .utils import get_ranking_model
from .utils import get_text_splitter
from .utils import get_vectorstore

logger = logging.getLogger(__name__)

#Defining the python actions 

# # Define the quiz response prompt template
quiz_response_template = """
Based on the following quiz question, DO NOT provide or hint at the correct answer.
Instead, explain the underlying concepts to help understanding.

Question: {question}

Concept Explanation (no answers):
"""

@action(is_system_action=True)
async def quiz_response(context: dict, llm: BaseLLM):
    logger.info("QUIZ RESPONSE ACTION TRIGGERED!")
    try:
        # Get the quiz question from the context
        inputs = context.get("last_user_message")
        logger.info(f"Processing quiz question: {inputs}")
        
        # Build the prompt chain
        output_parser = StrOutputParser()
        prompt_template = PromptTemplate.from_template(quiz_response_template)
        input_variables = {"question": inputs}
        chain = prompt_template | llm | output_parser
        
        # Invoke the chain to generate a response
        answer = await chain.ainvoke(input_variables)
        logger.info(f"Generated quiz response: {answer}")
        
        # Return an ActionResult with the answer and any context updates (if needed)
        return ActionResult(
            return_value="I understand you're asking about: " + answer,
            context_updates={}
        )
    except Exception as e:
        logger.error(f"Error in quiz_response: {e}")
        return ActionResult(
            return_value="I can help explain the concepts, but I cannot provide direct answers to quiz questions.",
            context_updates={}
        )

code_debug_response_template = """
Based on the code debugging question provided, DO NOT provide the exact solution or directly fix the code.
Instead, help guide the student through a debugging process by:
1. Explaining relevant programming concepts
2. Suggesting areas to investigate
3. Providing general debugging strategies
4. Asking guiding questions that help them discover the issue themselves

Question: {question}

Helpful debugging guidance (no direct solutions):
"""

@action(is_system_action=True)
async def code_debug_response(context: dict, llm: BaseLLM):
    logger.info("CODE DEBUG RESPONSE ACTION TRIGGERED!")
    try:
        # Get the debugging question from the context
        inputs = context.get("last_user_message")
        logger.info(f"Processing code debugging question: {inputs}")
        
        # Build the prompt chain
        output_parser = StrOutputParser()
        prompt_template = PromptTemplate.from_template(code_debug_response_template)
        input_variables = {"question": inputs}
        chain = prompt_template | llm | output_parser
        
        # Invoke the chain to generate a response
        answer = await chain.ainvoke(input_variables)
        logger.info(f"Generated code debugging guidance: {answer}")
        
        # Return an ActionResult with the answer and any context updates (if needed)
        return ActionResult(
            return_value="Let me help guide you through debugging this issue: " + answer,
            context_updates={}
        )
    except Exception as e:
        logger.error(f"Error in code_debug_response: {e}")
        return ActionResult(
            return_value="I can help you think through your debugging approach. Could you share more details about the issue you're facing?",
            context_updates={}
        )

homework_brainstorm_template = """
For this homework question, provide a structured brainstorming approach that helps the student develop their own solution. Include:

1. A breakdown of the key concepts involved
2. Multiple approaches or methodologies to consider
3. Relevant examples that illustrate the concepts (without solving the exact problem)
4. Questions the student should ask themselves while working
5. Resources they might consult for deeper understanding

Question: {question}

Brainstorming guidance (do not solve directly):
"""

@action(is_system_action=True)
async def homework_brainstorm(context: dict, llm: BaseLLM):
    logger.info("HOMEWORK BRAINSTORM ACTION TRIGGERED!")
    try:
        inputs = context.get("last_user_message")
        logger.info(f"Processing homework question: {inputs}")
        
        output_parser = StrOutputParser()
        prompt_template = PromptTemplate.from_template(homework_brainstorm_template)
        input_variables = {"question": inputs}
        chain = prompt_template | llm | output_parser
        
        answer = await chain.ainvoke(input_variables)
        logger.info(f"Generated homework brainstorming: {answer}")
        
        return ActionResult(
            return_value="Here's how you might approach this: " + answer,
            context_updates={}
        )
    except Exception as e:
        logger.error(f"Error in homework_brainstorm: {e}")
        return ActionResult(
            return_value="I'd suggest breaking down this problem into smaller parts and identifying the key concepts involved. What specific aspect are you finding challenging?",
            context_updates={}
        )

# #The next two actions is for document_summary.co
# document_summary_template = """
# Provide a comprehensive yet concise summary of the following document/lecture slides. Include:

# 1. The main topic or focus of the document
# 2. Key concepts, theories, or frameworks introduced
# 3. Important definitions, formulas, or methodologies
# 4. Major arguments, findings, or conclusions
# 5. How the information is structured or flows
# 6. Connections between different sections or ideas

# Document content: {document_content}

# Summary (organized by main sections):
# """

# @action(is_system_action=True)
# async def document_summary(context: dict, llm: BaseLLM):
#     logger.info("DOCUMENT SUMMARY ACTION TRIGGERED!")
#     try:
#         # Get the user message to identify which document they're asking about
#         user_message = context.get("last_user_message")
#         logger.info(f"Processing document summary request: {user_message}")
        
#         # Will have to fix this later to work with canvas grab
#         document_content = await retrieve_document_content(user_message, context)
        
#         if not document_content:
#             return ActionResult(
#                 return_value="I couldn't find the specific document you're referring to. Could you provide more details about which document or lecture slides you'd like me to summarize?",
#                 context_updates={}
#             )
        
#         output_parser = StrOutputParser()
#         prompt_template = PromptTemplate.from_template(document_summary_template)
#         input_variables = {"document_content": document_content}
#         chain = prompt_template | llm | output_parser
        
#         summary = await chain.ainvoke(input_variables)
#         logger.info(f"Generated document summary of length: {len(summary)}")
        
#         return ActionResult(
#             return_value=f"Here's a summary of the document:\n\n{summary}",
#             context_updates={"document_summary": summary}
#         )
#     except Exception as e:
#         logger.error(f"Error in document_summary: {e}")
#         return ActionResult(
#             return_value="I encountered an issue while trying to summarize the document. Could you specify which document you'd like me to summarize or try a different approach?",
#             context_updates={}
#         )

# Helper function to retrieve document content, we might not need this is retrieve_relvant_chunks is predefiuned
# async def retrieve_document_content(query: str, context: dict) -> str:
#     """
#     This function would need to be implemented to:
#     1. Parse the user query to identify which document they want
#     2. Retrieve the document from your storage/database
#     3. Extract and return the content
    
#     You could use the retrieve_relevant_chunks function as a starting point
#     and modify it to focus on retrieving entire documents instead of chunks.
#     """
    
#     try:
#         # Using your existing retrieve_relevant_chunks with modifications
#         retrieval_result = await retrieve_relevant_chunks(context, llm)
        
#         # Extract the full document content rather than just chunks
#         if isinstance(retrieval_result, ActionResult):
#             content = retrieval_result.return_value
#             # Process the content as needed
#             return content
#         return "Document content not found"
#     except Exception as e:
#         logger.error(f"Error retrieving document content: {e}")
#         return "Error retrieving document content"

@action(is_system_action=True)
async def process_course_content(context: dict, llm: BaseLLM):
    try:
        # Get the user's question
        user_message = context.get("last_user_message")
        logger.info(f"Processing course content for question: {user_message}")
        
        # Call retrieve_relevant_chunks to get the content
        retrieval_result = await retrieve_relevant_chunks(context, llm)
        
        # Process the retrieved chunks into a prompt
        prompt_template = PromptTemplate.from_template(
            "Based on the following course information, answer the question: {question}\n\n" +
            "Course information: {context}\n\n" +
            "Provide a clear, concise answer based only on the information provided above."
        )
        
        # Extract content from retrieval result
        if isinstance(retrieval_result, ActionResult):
            context_data = retrieval_result.return_value
        else:
            context_data = retrieval_result
        
        # Process through LLM
        chain = prompt_template | llm | StrOutputParser()
        answer = await chain.ainvoke({"question": user_message, "context": context_data})
        
        return ActionResult(
            return_value=answer,
            context_updates={"processed_course_content": answer}
        )
    except Exception as e:
        logger.error(f"Error in process_course_content: {e}")
        return ActionResult(
            return_value="I'm having trouble processing information about that course. Could you try asking in a different way?",
            context_updates={}
        )

VECTOR_STORE_PATH = "vectorstore.pkl"
document_embedder = get_embedding_model()
ranker = get_ranking_model()
TEXT_SPLITTER = None
settings = get_config()
prompts = get_prompts()
vector_db_top_k = int(os.environ.get("VECTOR_DB_TOPK", 40))

try:
    VECTOR_STORE = create_vectorstore_langchain(document_embedder=document_embedder)
except Exception as ex:
    VECTOR_STORE = None
    logger.info("Unable to connect to vector store during initialization: %s", ex)

# Initialize NeMo Guardrails
try:
    guardrails_path = os.environ.get(
        "GUARDRAILS_CONFIG_PATH",
        os.path.join(os.path.dirname(__file__), "guardrails", "config", "rails")
    )
    rails_config = RailsConfig.from_path(guardrails_path)
    logger.info(f"Computed guardrails_path: {guardrails_path}")
    print(f"DEBUG: Computed guardrails_path: {guardrails_path}")
        
    # Initialize rails without llm_params as it's not supported
    RAILS = LLMRails(rails_config)

    #I am registering the python actions here
    RAILS.register_action(quiz_response, "quiz_response")
    RAILS.register_action(code_debug_response, "code_debug_response")
    RAILS.register_action(homework_brainstorm, "homework_brainstorm")
    RAILS.register_action(process_course_content, "process_course_content")



    logger.info("Successfully initialized NeMo Guardrails and registered quiz_response")
    # After initialization, we can set the temperature if needed
    if 'temperature' in os.environ:
        RAILS.llm.temperature = float(os.environ.get("GUARDRAILS_TEMPERATURE", 0.2))
    
    logger.info("DEBUG: This is the chains.py file in directory X")
    logger.info(f"Successfully initialized NeMo Guardrails from path: {guardrails_path}")
except Exception as ex:
    RAILS = None
    logger.warning(f"Failed to initialize NeMo Guardrails: {ex}")


class UnstructuredRAG(BaseExample):

    def ingest_docs(self, data_dir: str, filename: str, collection_name: str = "") -> None:
        """Ingests documents to the VectorDB.
        It's called when the POST endpoint of `/documents` API is invoked.

        Args:
            data_dir (str): The path to the document file.
            filename (str): The name of the document file.
            collection_name (str): The name of the collection to be created in the vectorstore.

        Raises:
            ValueError: If there's an error during document ingestion or the file format is not supported.
        """
        try:
            # Load raw documents from the directory
            _path = data_dir
            raw_documents = UnstructuredFileLoader(_path).load()

            if raw_documents:
                global TEXT_SPLITTER  # pylint: disable=W0603
                # Get text splitter instance, it is selected based on environment variable APP_TEXTSPLITTER_MODELNAME
                # tokenizer dimension of text splitter should be same as embedding model
                if not TEXT_SPLITTER:
                    TEXT_SPLITTER = get_text_splitter()

                # split documents based on configuration provided
                logger.info(f"Using text splitter instance: {TEXT_SPLITTER}")
                documents = TEXT_SPLITTER.split_documents(raw_documents)
                vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
                # ingest documents into vectorstore
                vs.add_documents(documents)
            else:
                logger.warning("No documents available to process!")

        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the NIM model endpoint: %s", e)
            raise ValueError(
                    "Connection timed out while making a request to the embedding model endpoint. Verify if the server is available.") from e

        except Exception as e:
            print_exc()
            logger.error("Failed to ingest document due to exception %s", e)

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                raise ValueError(
                    "Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.") from e

            if "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                raise ValueError(
                    "Please verify the API endpoint and your payload. Ensure that the embedding model name is valid.") from e

            raise ValueError(f"Failed to upload document. {str(e)}") from e
    
    def _apply_guardrails(self, response: str, messages: List[tuple]) -> str:
        """Apply guardrails to the generated response."""
        try:
            if RAILS is None:
                logger.warning("Guardrails not initialized, returning original response")
                return response
                
            # Find the last user message
            #user_message = ""
            #for role, content in reversed(messages):
            #    if role == "user":
            #        user_message = content
             #       break
            
            #if not user_message:
            #    logger.warning("No user message found in conversation")
            #    return response
                
            # Generate response with guardrails - use proper message format
            # formatted_messages = [{
            #    "role": "user",
            #    "content": user_message
            # }]

            formatted_messages = [{"role": role, "content": content} for role, content in messages]

            logger.info(f"Sending to guardrails: {formatted_messages}")  # Add this log
            guarded_response = RAILS.generate(messages=formatted_messages)
            logger.info(f"Raw guardrails response: {guarded_response}")  # Add this log
            
            # If we get an empty response, return the original
            if not guarded_response:
                logger.warning("Empty guardrails response, using original")
                return response
                
            # Handle the response
            if isinstance(guarded_response, dict):
                if 'bot_message' in guarded_response and guarded_response['bot_message'].strip():
                    return guarded_response['bot_message']
                if 'content' in guarded_response and guarded_response['content'].strip():
                    return guarded_response['content']
                if 'response' in guarded_response and guarded_response['response'].strip():
                    return guarded_response['response']
            elif isinstance(guarded_response, str) and guarded_response.strip():
                return guarded_response

            
            logger.info("No specific guardrail triggered, using original response")
            return response
                
        except Exception as ex:
            logger.warning(f"Failed to apply guardrails: {ex}")
            return response

   
    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""
        logger.info("Using llm to generate response directly without knowledge base.")
        system_message = []
        conversation_history = []

        # Filter out empty messages and ensure valid content
        system_prompt = prompts.get("chat_template", "").strip()
        if not system_prompt:
            system_prompt = "You are a polite teaching assistant designed to help students learn."

        # Append personality instructions based on the provided persona.
        # Assume that the Prompt object (passed from server.py) has a 'persona' attribute.
        # We can check kwargs for a persona or have it available in the prompt.
        persona = kwargs.get("persona", "drill_sergeant").lower()
        
        # Get the configuration object to fetch persona instructions.
        config = get_config()
        if persona == "formal":
            personality_instructions = prompts.get("formal_persona", "")
        elif persona == "casual":
            personality_instructions = prompts.get("casual_persona", "")
        elif persona == "drill_sergeant":
            personality_instructions = prompts.get("drill_sergeant_persona", "")
        else:
            personality_instructions = ""  # default to no extra instructions if unknown

        if personality_instructions:
            system_prompt += " " + personality_instructions

        # incorporate any system messages provided in the chat history
        for message in chat_history:
            if message.role == "system":
                system_prompt = system_prompt + " " + message.content
            else:
                conversation_history.append((message.role, message.content))

        system_message = [("system", system_prompt)]
        user_message = [("user", query)]  # Changed from {question} to direct query

        # Prompt template with system message, conversation history and user query
        message = system_message + conversation_history + user_message
        self.print_conversation_history(message)

        try:
            prompt_template = ChatPromptTemplate.from_messages(message)
            llm = get_llm(**kwargs)
            
            # Get the raw response
            chain = prompt_template | llm | StrOutputParser()
            raw_response = ""
            for chunk in chain.stream({"question": query}):
                raw_response += chunk

            # Apply guardrails to the complete response
            guarded_response = self._apply_guardrails(raw_response, message)
            
            # Stream the guarded response
            if guarded_response and guarded_response.strip():
                for chunk in guarded_response.strip().split():
                    yield chunk + " "
            else:
                yield "I'm here to help. What would you like to know?"
                
        except Exception as e:
            logger.error(f"Error in llm_chain: {e}")
            yield "I apologize, but I encountered an error. Could you please rephrase your question?"

    def rag_chain(self, query: str, chat_history: List["Message"], top_n: int, 
                 collection_name: str = "", **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `True`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.
            top_n (int): Fetch n document to generate.
            collection_name (str): Name of the collection to be searched from vectorstore.
            kwargs: Additional keyword arguments for the LLM
        """

        if os.environ.get("ENABLE_MULTITURN", "false").lower() == "true":
            return self.rag_chain_with_multiturn(query, chat_history, top_n, collection_name, **kwargs)
            
        logger.info("Using rag to generate response from document for the query: %s", query)

        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs is None:
                logger.error("Vector store not initialized properly")
                raise ValueError()

            llm = get_llm(**kwargs)
            top_k = vector_db_top_k if ranker else top_n
            logger.info("Setting retriever top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})

            system_prompt = ""
            conversation_history = []
            system_prompt += prompts.get("rag_template", "")

            for message in chat_history:
                if message.role == "system":
                    system_prompt = system_prompt + " " + message.content

            system_message = [("system", system_prompt)]
            user_message = [("user", "{question}")]
            message = system_message + conversation_history + user_message
            
            self.print_conversation_history(message)
            prompt = ChatPromptTemplate.from_messages(message)

            if ranker:
                logger.info(
                    "Narrowing the collection from %s results and further narrowing it to "
                    "%s with the reranker for rag chain.",
                    top_k,
                    top_n)
                logger.info("Setting ranker top n as: %s.", top_n)
                ranker.top_n = top_n
                reranker = RunnableAssign({
                    "context": lambda input: ranker.compress_documents(
                        query=input['question'], 
                        documents=input['context']
                    )
                })

                retriever = {"context": retriever, "question": RunnablePassthrough()} | reranker
                docs = retriever.invoke(query)
                docs = [d.page_content for d in docs.get("context", [])]
            else:
                docs = retriever.invoke(query)
                docs = [d.page_content for d in docs]

            chain = prompt | llm | StrOutputParser()
            raw_response = ""
            for chunk in chain.stream({"question": query, "context": docs}):
                raw_response += chunk

            # Apply guardrails to the complete response
            guarded_response = self._apply_guardrails(raw_response, message)
            
            # Stream the guarded response
            for chunk in guarded_response.split():
                yield chunk + " "

        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the LLM endpoint: %s", e)
            yield "Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available."

        except Exception as e:
            logger.warning("Failed to generate response: %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                yield "Authentication or permission error: Verify the validity and permissions of your NVIDIA API key."
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                yield "Please verify the API endpoint and your payload. Ensure that the model name is valid."
            else:
                yield "Failed to generate response. Please ensure documents are ingested and try again."

    def rag_chain_with_multiturn(self,
                                query: str,
                                chat_history: List["Message"],
                                top_n: int,
                                collection_name: str,
                                **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain with multi-turn support."""

        logger.info("Using multiturn rag to generate response from document for the query: %s", query)

        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs is None:
                logger.error("Vector store not initialized properly. Please check if the vector db is up and running")
                raise ValueError()

            llm = get_llm(**kwargs)
            top_k = vector_db_top_k if ranker else top_n
            logger.info("Setting retriever top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})

            # conversation is tuple so it should be multiple of two
            # -1 is to keep last k conversation
            history_count = int(os.environ.get("CONVERSATION_HISTORY", 15)) * 2 * -1
            chat_history = chat_history[history_count:]
            system_prompt = ""
            conversation_history = []
            system_prompt += prompts.get("rag_template", "")

            for message in chat_history:
                if message.role == "system":
                    system_prompt = system_prompt + " " + message.content
                else:
                    conversation_history.append((message.role, message.content))

            system_message = [("system", system_prompt)]
            retriever_query = query
            
            if os.environ.get("ENABLE_QUERYREWRITER", "false").lower() == "true":
                # Based on conversation history recreate query for better document retrieval
                contextualize_q_system_prompt = (
                    "Given a chat history and the latest user question "
                    "which might reference context in the chat history, "
                    "formulate a standalone question which can be understood "
                    "without the chat history. Do NOT answer the question, "
                    "just reformulate it if needed and otherwise return it as is."
                )
                query_rewriter_prompt = prompts.get("query_rewriter_prompt", contextualize_q_system_prompt)
                contextualize_q_prompt = ChatPromptTemplate.from_messages(
                    [("system", query_rewriter_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}"),]
                )
                q_prompt = contextualize_q_prompt | llm | StrOutputParser()
                # query to be used for document retrieval
                logger.info("Query rewriter prompt: %s", contextualize_q_prompt)
                retriever_query = q_prompt.invoke({"input": query, "chat_history": conversation_history})
                logger.info("Rewritten Query: %s %s", retriever_query, len(retriever_query))
                if retriever_query.replace('"', "'") == "''" or len(retriever_query) == 0:
                    return iter([""])

            # Prompt for response generation based on context
            user_message = [("user", "{question}")]

            # Prompt template with system message, conversation history and user query
            message = system_message + conversation_history + user_message
            self.print_conversation_history(message)
            prompt = ChatPromptTemplate.from_messages(message)

            if ranker:
                logger.info(
                    "Narrowing the collection from %s results and further narrowing it to "
                    "%s with the reranker for rag chain.",
                    top_k,
                    settings.retriever.top_k)
                logger.info("Setting ranker top n as: %s.", top_n)
                ranker.top_n = top_n
                context_reranker = RunnableAssign({
                    "context":
                        lambda input: ranker.compress_documents(query=input['question'], documents=input['context'])
                })

                retriever = {"context": retriever, "question": RunnablePassthrough()} | context_reranker
                docs = retriever.invoke(retriever_query)
                docs = [d.page_content for d in docs.get("context", [])]
            else:
                docs = retriever.invoke(retriever_query)
                docs = [d.page_content for d in docs]

            chain = prompt | llm | StrOutputParser()
            raw_response = ""
            for chunk in chain.stream({"question": f"{query}", "context": docs}):
                raw_response += chunk

            # Apply guardrails to the complete response
            guarded_response = self._apply_guardrails(raw_response, message)
            
            # Stream the guarded response
            for chunk in guarded_response.split():
                yield chunk + " "

        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the LLM endpoint: %s", e)
            yield "Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available."

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                yield "Authentication or permission error: Verify the validity and permissions of your NVIDIA API key."
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                yield "Please verify the API endpoint and your payload. Ensure that the model name is valid."
            else:
                yield "No response generated from LLM, make sure you have ingested document from the Knowledge Base Tab."

    def document_search(self, content: str, num_docs: int, collection_name: str = "") -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters.
        It's called when the `/search` API is invoked.

        Args:
            content (str): Query to be searched from vectorstore.
            num_docs (int): Number of similar docs to be retrieved from vectorstore.
            collection_name (str): Name of the collection to be searched from vectorstore.
        """

        logger.info("Searching relevant document for the query: %s", content)

        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs is None:
                logger.error("Vector store not initialized properly. Please check if the vector db is up and running")
                raise ValueError()

            docs = []
            local_ranker = get_ranking_model()
            top_k = vector_db_top_k if local_ranker else num_docs
            logger.info("Setting top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})

            if local_ranker:
                logger.info(
                    "Narrowing the collection from %s results and further narrowing it to %s with the reranker for rag"
                    " chain.",
                    top_k,
                    num_docs)
                logger.info("Setting ranker top n as: %s.", num_docs)
                # Update number of document to be retriever by ranker
                local_ranker.top_n = num_docs

                context_reranker = RunnableAssign({
                    "context":
                        lambda input: local_ranker.compress_documents(query=input['question'],
                                                                    documents=input['context'])
                })

                retriever = {"context": retriever, "question": RunnablePassthrough()} | context_reranker
                docs = retriever.invoke(content)
                resp = []
                for doc in docs.get("context"):
                    resp.append({
                        "source": os.path.basename(doc.metadata.get("source", "")),
                        "content": doc.page_content,
                        "score": doc.metadata.get("relevance_score", 0)
                    })
                return resp

            docs = retriever.invoke(content)
            resp = []
            for doc in docs:
                resp.append({
                    "source": os.path.basename(doc.metadata.get("source", "")),
                    "content": doc.page_content,
                    "score": doc.metadata.get("relevance_score", 0)
                })
            return resp

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

        return []

    def get_documents(self, collection_name: str = "") -> List[str]:
        """Retrieves filenames stored in the vector store.
        It's called when the GET endpoint of `/documents` API is invoked.

        Returns:
            List[str]: List of filenames ingested in vectorstore.
        """
        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs:
                return get_docs_vectorstore_langchain(vs)
        except Exception as e:
            logger.error("Vectorstore not initialized. Error details: %s", e)

        return []

    def delete_documents(self, filenames: List[str], collection_name: str = "") -> bool:
        """Delete documents from the vector index.
        It's called when the DELETE endpoint of `/documents` API is invoked.

        Args:
            filenames (List[str]): List of filenames to be deleted from vectorstore.
            collection_name (str): Name of the collection to be deleted from vectorstore.
        """
        try:
            # Get vectorstore instance
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs:
                return del_docs_vectorstore_langchain(vs, filenames)
        except Exception as e:
            logger.error("Vectorstore not initialized. Error details: %s", e)
        return False

    def print_conversation_history(self, conversation_history: List[str] = None, query: str | None = None):
        """Print conversation history for debugging purposes."""
        if conversation_history is not None:
            for role, content in conversation_history:
                logger.info("Role: %s", role)
                logger.info("Content: %s\n", content)
        if query is not None:
            logger.info("Query: %s\n", query)

    
