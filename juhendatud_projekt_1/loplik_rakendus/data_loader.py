import os

import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer

from config import DATA_CSV, DATA_EMBEDDINGS, TEST_CASES_FILE


@st.cache_resource
def get_models():
    embedder = SentenceTransformer("BAAI/bge-m3")
    df = pd.read_csv(DATA_CSV)
    embeddings_df = pd.read_pickle(DATA_EMBEDDINGS)

    test_cases_df = pd.DataFrame()
    if os.path.exists(TEST_CASES_FILE):
        test_cases_df = pd.read_csv(TEST_CASES_FILE)

    return embedder, df, embeddings_df, test_cases_df
