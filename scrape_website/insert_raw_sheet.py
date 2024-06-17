import openai
import pinecone
from transformers import GPT2TokenizerFast

import settings


def init_pinecone():
    pinecone.init(
        api_key=settings.PINECONE_API_KEY,
        environment=settings.PINECONE_ENV
    )


def count_tokens(text: str) -> int:
    """count the number of tokens in a string"""
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    return len(tokenizer.encode(text))


def create_sample_embedding():
    res = openai.Embedding.create(
        input=[
            "Sample document text goes here",
        ], engine=settings.EMBEDDING_MODEL
    )

    # extract embeddings to a list
    embeds = [record['embedding'] for record in res['data']]

    return embeds[0]


def get_pinecone_index(pine_index):
    if pine_index not in pinecone.list_indexes():
        pinecone.create_index(pine_index, dimension=len(create_sample_embedding()))
    # connect to index
    index = pinecone.Index(pine_index)
    return index


def insert_raw_data(data, namespace, index_name):
    dataset = []
    dataset_urls = []
    vec_ids = []
    for k in data:
        if k[0] == "" or k[0] == "content":
            continue
        dataset.append(k[0])
        dataset_urls.append(k[2])
        vec_ids.append(str(k[1]))
    batch_size = 32  # process everything in batches of 32
    pinecone_index = get_pinecone_index(index_name)
    for i in range(0, len(dataset), batch_size):
        lines_batch = []
        ids_batch = []
        # set end position of batch
        i_end = min(i + batch_size, len(dataset))
        # get batch of lines and IDs
        lines_batch = dataset[i: i_end]
        ids_batch = vec_ids[i:i_end]
        urls_batch = dataset_urls[i: i_end]
        # create embeddings
        res = openai.Embedding.create(input=list(lines_batch), engine=settings.EMBEDDING_MODEL)
        embeds = [record['embedding'] for record in res.data]
        # prep metadata and upsert batch
        meta = [{'title': line, "url": urls_batch[idx]} for idx, line in enumerate(list(lines_batch))]
        to_upsert = zip(ids_batch, embeds, meta)
        # upsert to Pinecone
        pinecone_index.upsert(vectors=list(to_upsert), namespace=namespace)
