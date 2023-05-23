import json
import os
import pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma, Pinecone
import pandas as pd
import numpy as np

#  If true, this will populate the pinecone vector database with new embeddings.
#  If already have, no need to make true, or run this script.
CREATE_NEW_HPO_EMBEDDINGS = False


def gather_definition(meta_dict):
    if isinstance(meta_dict, dict):
        if 'definition' in meta_dict.keys():
            return meta_dict['definition']['val']
        else:
            return np.nan
    else:
        return np.nan


def gather_comments(meta_dict):
    if isinstance(meta_dict, dict):
        if 'comments' in meta_dict.keys():
            return meta_dict['comments']
        else:
            return np.nan
    else:
        return np.nan


def str_to_embed(df_row):
    string_template = ""
    if pd.notnull(df_row['lbl']):
        string_template += f"label: {df_row['lbl']} \n"
    if pd.notnull(df_row['definition']):
        string_template += f"definition: {df_row['definition']} \n"
    if pd.notnull(df_row['comments']):
        string_template += "comments: "
        for comment in df_row['comments']:
            string_template += f"{comment} \n"
    return string_template


if __name__ == "__main__":
    with open('hp.json') as f:
        data = json.load(f)

    hpo_data = data['graphs'][0]['nodes']
    hpo_data_df = pd.DataFrame(hpo_data)

    simple_hpo_df = pd.DataFrame(columns=['id', 'lbl', 'definition', 'comments'])

    simple_hpo_df['id'] = hpo_data_df['id'].apply(lambda x: str(x)[-10:])
    simple_hpo_df['lbl'] = hpo_data_df['lbl']
    simple_hpo_df['definition'] = hpo_data_df['meta'].apply(gather_definition)
    simple_hpo_df['comments'] = hpo_data_df['meta'].apply(gather_comments)

    simple_hpo_df['text_to_embed'] = simple_hpo_df.apply(str_to_embed, axis=1)

    #print(simple_hpo_df['text_to_embed'][98])

    embedding = OpenAIEmbeddings(openai_api_key=os.environ['OPENAI_API_KEY'])
    pinecone.init(
        api_key=os.environ['PINECONE_API_KEY'],
        environment=os.environ['PINECONE_API_ENV']
    )
    index_name = "hpo-embeddings"
    index = pinecone.Index(index_name)

    # only run once to embed hpo terms
    if CREATE_NEW_HPO_EMBEDDINGS:
        embsearch = Pinecone.from_texts(simple_hpo_df['text_to_embed'].tolist(), embedding, index_name=index_name)

    vectorstore = Pinecone(index=index, embedding_function=embedding.embed_query, text_key='text')
