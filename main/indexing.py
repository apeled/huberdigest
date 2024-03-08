#!/usr/bin/env python
# coding: utf-8

"""This file creates and stores an VectorStoreIndex for usage in our streamlit application.

Notebook contents:
1. Load JSON transcripts.
2. Parse transcript sections into Documents and attaches metadata.
3. Extract keywords and embeds nodes using the OpenAI API.
4. Create VectorStoreIndex from the nodes and stores it locally.
5. Test reloading the index.
6. Create and test a simple retrieval engine using embeddings.

Modules: os, json, time, nest_asyncio, pickle, llama_index libraries.

Author: Edouard Seryozhenkov
Date: 2024-02-29
"""

import json
import os
import time
import nest_asyncio
import pickle as pkl

from llama_index.core import Document, VectorStoreIndex, get_response_synthesizer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.extractors import (
    KeywordExtractor,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.schema import MetadataMode
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI


nest_asyncio.apply()

def load_json_transcripts(base_path: str) -> list:
    """Loads all JSON transcript files from the specified base path.

    Args:
        base_path (str): The path to the directory containing the transcript files.

    Returns:
        list: A list containing all parsed transcript data as JSON objects.
            An empty list is returned if no valid transcripts are found.
    """
    podcasts_as_json = []
    for filename in os.listdir(base_path):
        if filename.endswith(".json"):
            path = base_path + "/" + filename
            with open(path, "r") as file:
                podcasts_as_json.append(json.load(file))

    return podcasts_as_json

def parse_into_documents(podcast_jsons: list) -> list[Document]:
    """Parses a list of JSON transcripts into a list of Document objects.

    For each transcript:

    1. Extracts essential metadata like episode title, number, summary, and YouTube link.
    2. Creates a list of document subsections ("chunks") from the transcript's "chunks" key.
    3. For each chunk:
        - Creates a copy of the transcript metadata to avoid modifying the original.
        - Adds the chunk's timestamp to the metadata.
        - Initializes a Document object with the chunk's text and the modified metadata.
        - Excludes specified metadata keys (episode_summary, timestamp, youtube_link) from
            both LLM and embed processing within the Document object.
        - Appends the created Document object to a list.

    Finally, the function returns the constructed list of Document objects.

    Args:
        podcast_jsons (list): A list of JSON objects, each representing a podcast transcript.

    Returns:
        list[Document]: A list of Document objects containing parsed transcript data and 
                            metadata from each input JSON. An empty list is returned if no valid 
                            transcripts are provided.
    """
    doc_list = []
    for pc_json in podcast_jsons:
        podcast_metadata = {
            "episode_title": pc_json["title"],
            "episode_number": pc_json["ep_num"],
            "episode_summary": pc_json["episode_summary"],
            "youtube_link": pc_json["link"],
        }
        chunk_list = [chunk for chunk in pc_json["chunks"]]
        for chunk in chunk_list:
            chunk_metadata = podcast_metadata.copy()
            chunk_metadata["timestamp"] = chunk["timestamp"]
            chunk_text = chunk["text"]
            doc = Document(text=chunk_text, metadata=chunk_metadata)
            doc.excluded_embed_metadata_keys = [
                "episode_summary",
                "timestamp",
                "youtube_link",
            ]
            doc.excluded_llm_metadata_keys = [
                "episode_summary",
                "timestamp",
                "youtube_link",
            ]
            doc_list.append(doc)
    return doc_list


def get_simple_hube_engine(documents):
    """Makes a simple query engine that uses only the embeddings. Returns
        the context that would be fetched for the LLM, up to 20 nodes.

    Args:
        documents: A list of Document objects corresponding to podcast subsections

    Returns:
        query engine: An engine in "no_text" response mode
    """
    # Build a simple index from documents
    index = VectorStoreIndex.from_documents(documents)

    # Configure a retriever using this index
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=20,
    )

    # Configure response synthesizer
    response_synthesizer = get_response_synthesizer(response_mode="no_text")

    # Assemble the query engine
    simple_hube_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)],
    )

    return simple_hube_engine


"""This cell contains helper functions to serialize and load nodes from storage"""
def dump_object(x, filename="x.pkl"):
    # Writes Python object to a file using pickle
    with open(filename, "wb") as file:
        pkl.dump(x, file)

def load_object(filename):
    with open(filename, "rb") as file:
        obj = pkl.load(file)
        return obj

def unpickle_nodes(base_path):
    unpickled_nodes = []
    for filename in os.listdir(base_path):
        if filename.endswith(".pkl"):
            path = os.path.join(base_path, filename)
            nodes = load_object(path)
            unpickled_nodes.extend(nodes)
    return unpickled_nodes

def process_documents(
    documents: list[Document],
    start_index: int = 0,
    batch_size: int = 15,
) -> int:
    """Processes a list of Document objects using a ingestion pipeline, including:

    1. Sentence splitting: Splits documents into smaller sentences for easier processing.
    2. Keyword extraction: Extracts the top keywords from each document.
    3. OpenAI embedding: Generates embeddings for each document using the specified OpenAI model.

    Each batch is processed using the `IngestionPipeline`, and the resulting data is then serialized.

    Args:
        documents (list[Document]): A list of documents to be processed.
        start_index (int, optional): The index at which to start processing. Defaults to 0.
        batch_size (int, optional): The number of documents to process in each batch.
                                    Defaults to 15.

    Returns:
        int: Returns 0 to indicate successful completion.
    """
    my_transformations = [
        SentenceSplitter(chunk_size=1024),
        KeywordExtractor(keywords=5),
        OpenAIEmbedding(model="text-embedding-3-small"),
    ]
    pipeline = IngestionPipeline(transformations=my_transformations)
    for i in range(start_index, len(documents), batch_size):
        if i + batch_size < len(documents):
            batch = documents[i : i + batch_size]
            nodes = pipeline.run(documents=batch)
            dump_object(nodes, filename=f"nodes_{i}.pkl")
        else:
            # Last batch
            batch = documents[i:]
            nodes = pipeline.run(documents=batch)
            dump_object(nodes, filename=f"nodes_final.pkl")
        # Wait to avoid exceeding OpenAI rate limits
        time.sleep(60)
    return 0

def get_mid_video_link(link, t):
    """Modifies YouTube link to start at the specified time (seconds)."""
    base_url = link.replace("www.youtube.com/watch?v=", "youtu.be/")
    return base_url + "?t=" + str(t)


def extract_metadata(response):
    """Extracts and transforms metadata from source nodes in a query response. """
    metadata_list = [node.metadata for node in response.source_nodes]
    for metadata in metadata_list:
        base_link = metadata["youtube_link"]
        start_time = metadata["timestamp"]
        metadata["youtube_link"] = get_mid_video_link(base_link, start_time)
    return metadata_list

# Using GPT-3.5 for keyword extraction because it is cheaper
Settings.llm = OpenAI(temperature=0.2, model="gpt-3.5-turbo-0125")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

# Parse the transcripts into Documents
##### This ideally would reference the merge_rss_and_transcrpt module ##########
################################################################################
podcast_jsons = load_json_transcripts("/home/edouas/DATA-515/TLDhubeR/transcript_data")
################################################################################
documents = parse_into_documents(podcast_jsons)
len(documents)

# Process the documents into lists of nodes and serialize
process_documents(documents, batch_size=15)

nodes = unpickle_nodes("/home/edouas/DATA-515/TLDhubeR/pickled_nodes/")
dump_object(nodes, "nodes_full.pkl")

# Load all the nodes into a single list
nodes = load_object("/home/edouas/DATA-515/TLDhubeR/pickled_nodes/nodes_full.pkl")
len(nodes)

# Make sure the correct metadata was exposed to the LLM and the embedding model
print(nodes[0].get_content(metadata_mode=MetadataMode.LLM))
print(nodes[0].get_content(metadata_mode=MetadataMode.EMBED))

from llama_index.core import StorageContext, load_index_from_storage

# Construct vector store and customize storage context
storage_context = StorageContext.from_defaults()

# Create (or load) docstore and add nodes
storage_context.docstore.add_documents(nodes)

# Build index
index = VectorStoreIndex(nodes, embed_model=Settings.embed_model, storage_context=storage_context)

# Save index
index.storage_context.persist(persist_dir="./data")

# Rebuild storage context from directory
storage_context_load = StorageContext.from_defaults(persist_dir="./data")

# Test reloading the index
loaded_index = load_index_from_storage(storage_context_load)

# Testing by configuring a retriever using this index
retriever = VectorIndexRetriever(
    index=loaded_index,
    similarity_top_k=20,
)

# Configure response synthesizer
response_synthesizer = get_response_synthesizer(response_mode="no_text")

# Assemble the query engine
simple_hube_engine = RetrieverQueryEngine.from_args(
    retriever=retriever,
    response_synthesizer=response_synthesizer,
    node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.25)],
)

# Testing semantic searching (node retrieval) using a few sample queries
response = simple_hube_engine.query("david goggins")
response.source_nodes

response2 = simple_hube_engine.query("The dangers of social media.")
response2.source_nodes

