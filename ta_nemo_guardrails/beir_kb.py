from nemoguardrails.kb.kb import KnowledgeBase
import hashlib
import logging
import os
from time import time
from typing import Callable, List, Optional, cast
import json 

from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem
from nemoguardrails.kb.utils import split_markdown_in_topic_chunks
from nemoguardrails.rails.llm.config import EmbeddingSearchProvider, KnowledgeBaseConfig

"""
Example of corpus formatting

{
    "0": {
        "title": "Assignment Review - \"Student Roles\" - 0",
        "text": "<link rel=\"stylesheet\" href=\"https://instructure-uploads.s3.us-east-1.amazonaws.com/account_12150000000000001/attachments/6025727/mobile%20app.css\"><p>In this module, we will be going over last module's assignment where you were split into groups that had different roles for submitting an assignment to Gradescope. We will talk about why the code you submitted passed or failed some test cases to introduce you to how the Autograder grades program output. We will also look at how to make an autograder and upload it to gradescope in preparation for next module's assignment.&nbsp;</p>",
        "metadata": {
            "source_document_name": "Assignment Review - \"Student Roles\"",
            "sequence_number": 0
        }
    },
    "1": {
        "title": "Audograder Design - 0",
        "text": "<link rel=\"stylesheet\" href=\"https://instructure-uploads.s3.us-east-1.amazonaws.com/account_12150000000000001/attachments/6025727/mobile%20app.css\"><p>In this module, we will go over some high level design considerations for autograding student assignments, and you will have the opportunity to design some sample test cases.</p>",
        "metadata": {
            "source_document_name": "Audograder Design",
            "sequence_number": 0
        }
    },
    "2": {
        "title": "Autograder Implementation - 0",
        "text": "<link rel=\"stylesheet\" href=\"https://instructure-uploads.s3.us-east-1.amazonaws.com/account_12150000000000001/attachments/6025727/mobile%20app.css\"><p>In this module, you will learn how to implement your test cases in an autograder that can be run on Gradescope. Then you will complete an assignment to give you some practice on setting up autograder tests.</p>",
        "metadata": {
            "source_document_name": "Autograder Implementation",
            "sequence_number": 0
        }
    },
    "3": {
        "title": "Autograder Structure - 0",
        "text": "<link rel=\"stylesheet\" href=\"https://instructure-uploads.s3.us-east-1.amazonaws.com/account_12150000000000001/attachments/6025727/mobile%20app.css\"><p>Watch the following video from 18:20 to 25:47.</p>\n<p><iframe title=\"YouTube video player\" src=\"https://www.youtube.com/embed/ZX3G5dFRZKI?si=CdKsH3CYAVYtIBOk&amp;start=1100&amp;end=1546\" width=\"560\" height=\"315\" allowfullscreen=\"allowfullscreen\" allow=\"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share\"></iframe></p>",
        "metadata": {
            "source_document_name": "Autograder Structure",
            "sequence_number": 0
        }
    },
    "4": {
        "title": "Autograding Best Practices - 0",
        "text": "<link rel=\"stylesheet\" href=\"https://instructure-uploads.s3.us-east-1.amazonaws.com/account_12150000000000001/attachments/6025727/mobile%20app.css\"><p>Read through Gradescope's documentation covering <a class=\"inline_disabled\" title=\"Link\" href=\"https://gradescope-autograders.readthedocs.io/en/latest/best_practices/\" target=\"_blank\">Best Practices for Autograding</a>.</p>",
        "metadata": {
            "source_document_name": "Autograding Best Practices",
            "sequence_number": 0
        }
    },

"""

class BEIRKnowledgeBase(KnowledgeBase):
    # Overriding the init(self) method from the KnowledgeBase class
     def init(self):
        """Initialize the knowledge base.

        The initial data is loaded from the `$kb_docs` context key. The key is populated when
        the model is loaded. Currently, only markdown format is supported.
        """
        if not self.documents:
            return

        # Start splitting every doc into topic chunks

        for doc in self.documents:
            # Each document is a corpus
            print("DOC IS: ", doc)
            exit(1)
