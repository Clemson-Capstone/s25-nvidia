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
"""The definition of the application configuration."""
from .configuration_wizard import ConfigWizard
from .configuration_wizard import configclass
from .configuration_wizard import configfield


@configclass
class VectorStoreConfig(ConfigWizard):
    """Configuration class for the Vector Store connection.

    :cvar name: Name of vector store
    :cvar url: URL of Vector Store
    """

    name: str = configfield(
        "name",
        default="milvus",
        help_txt="The name of vector store",  # supports milvus
    )
    url: str = configfield(
        "url",
        default="http://milvus:19530",
        help_txt="The host of the machine running Vector Store DB",
    )
    nlist: int = configfield(
        "nlist",
        default=64,
        help_txt="Number of cluster units",  # IVF Flat milvus
    )
    nprobe: int = configfield(
        "nprobe",
        default=16,
        help_txt="Number of units to query",  # IVF Flat milvus
    )
    index_type: str = configfield(
        "index_type",
        default="GPU_IVF_FLAT",
        help_txt="Index of the vector db",  # IVF Flat for milvus
    )


@configclass
class LLMConfig(ConfigWizard):
    """Configuration class for the llm connection.

    :cvar server_url: The location of the llm server hosting the model.
    :cvar model_name: The name of the hosted model.
    """

    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The location of the Triton server hosting the llm model.",
    )
    model_name: str = configfield(
        "model_name",
        default="ensemble",
        help_txt="The name of the hosted model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="nvidia-ai-endpoints",
        help_txt="The server type of the hosted model. Allowed values are nvidia-ai-endpoints",
    )
    model_name_pandas_ai: str = configfield(
        "model_name_pandas_ai",
        default="ai-mixtral-8x7b-instruct",
        help_txt="The name of the ai catalog model to be used with PandasAI agent",
    )


@configclass
class TextSplitterConfig(ConfigWizard):
    """Configuration class for the Text Splitter.

    :cvar chunk_size: Chunk size for text splitter. Tokens per chunk in token-based splitters.
    :cvar chunk_overlap: Text overlap in text splitter.
    """

    model_name: str = configfield(
        "model_name",
        default="Snowflake/snowflake-arctic-embed-l",
        help_txt="The name of Sentence Transformer model used for SentenceTransformer TextSplitter.",
    )
    chunk_size: int = configfield(
        "chunk_size",
        default=510,
        help_txt="Chunk size for text splitting.",
    )
    chunk_overlap: int = configfield(
        "chunk_overlap",
        default=200,
        help_txt="Overlapping text length for splitting.",
    )


@configclass
class EmbeddingConfig(ConfigWizard):
    """Configuration class for the Embeddings.

    :cvar model_name: The name of the huggingface embedding model.
    """

    model_name: str = configfield(
        "model_name",
        default="snowflake/arctic-embed-l",
        help_txt="The name of huggingface embedding model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="nvidia-ai-endpoints",
        help_txt="The server type of the hosted model. Allowed values are hugginface",
    )
    dimensions: int = configfield(
        "dimensions",
        default=1024,
        help_txt="The required dimensions of the embedding model. Currently utilized for vector DB indexing.",
    )
    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The url of the server hosting nemo embedding model",
    )


@configclass
class RankingConfig(ConfigWizard):
    """Configuration class for the Re-ranking.

    :cvar model_name: The name of the Ranking model.
    """

    model_name: str = configfield(
        "model_name",
        default="nv-rerank-qa-mistral-4b:1",
        help_txt="The name of Ranking model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="nvidia-ai-endpoints",
        help_txt="The server type of the hosted model. Allowed values are nvidia-ai-endpoints",
    )
    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The url of the server hosting nemo Ranking model",
    )


@configclass
class RetrieverConfig(ConfigWizard):
    """Configuration class for the Retrieval pipeline.

    :cvar top_k: Number of relevant results to retrieve.
    :cvar score_threshold: The minimum confidence score for the retrieved values to be considered.
    """

    top_k: int = configfield(
        "top_k",
        default=4,
        help_txt="Number of relevant results to retrieve",
    )
    score_threshold: float = configfield(
        "score_threshold",
        default=0.25,
        help_txt="The minimum confidence score for the retrieved values to be considered",
    )
    nr_url: str = configfield(
        "nr_url",
        default='http://retrieval-ms:8000',
        help_txt="The nemo retriever microservice url",
    )
    nr_pipeline: str = configfield(
        "nr_pipeline",
        default='ranked_hybrid',
        help_txt="The name of the nemo retriever pipeline one of ranked_hybrid or hybrid",
    )

@configclass
class PersonaConfig(ConfigWizard):
    """Configuration for personality instructions."""
    formal: str = configfield(
        "formal",
        default="Please use formal language, maintain a professional tone, and provide detailed, precise explanations.",
        help_txt="Formal personality instructions."
    )
    casual: str = configfield(
        "casual",
        default="Use a friendly, casual tone with simple language and a conversational style.",
        help_txt="Casual personality instructions."
    )
    drill_sergeant: str = configfield(
        "drill_sergeant",
        default="Adopt a commanding and authoritative tone with clear, direct instructions. Speak as a drill sergeant who emphasizes discipline, precision, and unwavering focus. Provide concise guidance in a no-nonsense style.",
        help_txt="Drill sergeant personality instructions."
    )
    enthusiastic: str = configfield(
        "enthusiastic",
        default="Adopt an enthusiastic tone with high energy and excitement! Use exclamation points and upbeat language to motivate and engage the student.",
        help_txt="Enthusiastic personality instructions."
    )
    supportive: str = configfield(
        "supportive",
        default="Speak as a supportive significant other: warm, caring, and encouraging. Validate the student's efforts and provide gentle, affirming guidance.",
        help_txt="Supportive personality instructions."
    )
    meme_lord: str = configfield(
        "meme_lord",
        default="Adopt a meme lord style with playful language, occasional internet slang, and references to popular memes to make the conversation lighthearted and fun.",
        help_txt="Meme lord personality instructions."
    )
    humorous: str = configfield(
        "humorous",
        default="Adopt a witty and humorous tone with puns, jokes, and clever wordplay to make learning entertaining while still informative.",
        help_txt="Humorous personality instructions."
    )

@configclass
class AppConfig(ConfigWizard):
    """Configuration class for the application.

    :cvar vector_store: The configuration of the vector db connection.
    :type vector_store: VectorStoreConfig
    :cvar llm: The configuration of the backend llm server.
    :type llm: LLMConfig
    :cvar text_splitter: The configuration for text splitter
    :type text_splitter: TextSplitterConfig
    :cvar embeddings: The configuration for huggingface embeddings
    :type embeddings: EmbeddingConfig
    :cvar prompts: The Prompts template for RAG and Chat
    :type prompts: PromptsConfig
    """

    vector_store: VectorStoreConfig = configfield(
        "vector_store",
        env=False,
        help_txt="The configuration of the vector db connection.",
        default=VectorStoreConfig(),
    )
    llm: LLMConfig = configfield(
        "llm",
        env=False,
        help_txt="The configuration for the server hosting the Large Language Models.",
        default=LLMConfig(),
    )
    text_splitter: TextSplitterConfig = configfield(
        "text_splitter",
        env=False,
        help_txt="The configuration for text splitter.",
        default=TextSplitterConfig(),
    )
    embeddings: EmbeddingConfig = configfield(
        "embeddings",
        env=False,
        help_txt="The configuration of embedding model.",
        default=EmbeddingConfig(),
    )
    ranking: RankingConfig = configfield(
        "ranking",
        env=False,
        help_txt="The configuration of ranking model.",
        default=RankingConfig(),
    )
    retriever: RetrieverConfig = configfield(
        "retriever",
        env=False,
        help_txt="The configuration of the retriever pipeline.",
        default=RetrieverConfig(),
    )
    personas: PersonaConfig = configfield(
        "personas",
        env=False,
        help_txt="The persona instructions for the assistant.",
        default=PersonaConfig(),
    )

