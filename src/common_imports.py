"""
Common imports to reduce redundancy across modules
"""

# Standard library imports
import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

# Third-party imports
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# LangChain imports
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    HUGGINGFACE_NEW = True
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        HUGGINGFACE_NEW = False
    except ImportError:
        HuggingFaceEmbeddings = None
        HUGGINGFACE_NEW = False

# Qdrant imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# Local imports
from config import Config
from utils import Logger
