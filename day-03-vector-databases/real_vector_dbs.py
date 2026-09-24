"""
real_vector_dbs.py

This file is different from the others in this folder: it's not meant to
be run. It won't connect to anything, and there are no API keys here.

Instead, this shows what the CODE looks like when you use a real vector
database, so you can compare it to SimpleVectorDB and see that the ideas
are identical -- add vectors, search vectors -- just with production-grade
infrastructure behind the scenes.

Each function below is commented out on purpose. If you want to actually
run one of these, install the matching package, add your own API key, and
uncomment the code.
"""


def pinecone_example():
    """
    Pinecone: fully managed, cloud-hosted. You never run a server yourself.
    Good fit when you want to move fast and not manage infrastructure.

    Pricing: has a free tier for small projects; paid plans scale with the
    number of vectors stored and queries per second.
    """
    example_code = '''
    from pinecone import Pinecone

    # Get an API key from https://www.pinecone.io -- keep it in an
    # environment variable, never hardcode it in your code.
    pc = Pinecone(api_key="YOUR_API_KEY")

    # Create an index once. "dimension" must match your embedding model's
    # output size (e.g. 1536 for OpenAI's text-embedding-3-small).
    pc.create_index(name="my-documents", dimension=1536, metric="cosine")
    index = pc.Index("my-documents")

    # Add vectors -- same idea as SimpleVectorDB.add(), just at scale.
    index.upsert(vectors=[
        {"id": "doc1", "values": [0.1, 0.2, ...], "metadata": {"title": "What is RAG"}},
        {"id": "doc2", "values": [0.3, 0.1, ...], "metadata": {"title": "What is Python"}},
    ])

    # Search -- same idea as SimpleVectorDB.search().
    results = index.query(vector=[0.12, 0.19, ...], top_k=3, include_metadata=True)
    '''
    print("--- Pinecone ---")
    print(example_code)


def milvus_example():
    """
    Milvus: open source, self-hosted, built for very large scale (billions
    of vectors). You run it yourself, usually via Docker Compose.

    Pricing: free if you self-host (you pay for your own servers). There's
    also a managed version called Zilliz Cloud if you don't want to run it
    yourself.
    """
    docker_setup = '''
    # docker-compose.yml (simplified) -- run with: docker compose up -d
    services:
      milvus:
        image: milvusdb/milvus:latest
        ports:
          - "19530:19530"
    '''

    example_code = '''
    from pymilvus import MilvusClient

    # Connects to your self-hosted Milvus instance (or Zilliz Cloud).
    client = MilvusClient(uri="http://localhost:19530")

    client.create_collection(collection_name="my_documents", dimension=1536)

    # Add vectors.
    client.insert(collection_name="my_documents", data=[
        {"id": 1, "vector": [0.1, 0.2, ...], "title": "What is RAG"},
        {"id": 2, "vector": [0.3, 0.1, ...], "title": "What is Python"},
    ])

    # Search.
    results = client.search(
        collection_name="my_documents",
        data=[[0.12, 0.19, ...]],
        limit=3,
    )
    '''
    print("--- Milvus ---")
    print("Setup (docker-compose.yml):")
    print(docker_setup)
    print("Usage:")
    print(example_code)


def weaviate_example():
    """
    Weaviate: open source, available self-hosted or fully managed. Comes
    with extra built-in features, like combining keyword search and vector
    search together in one query (hybrid search) -- which is genuinely
    useful, since keyword and embedding search each catch different things,
    as we saw back in Day 2's comparison.py.

    Pricing: free if self-hosted; managed cloud plans scale with data size
    and usage.
    """
    example_code = '''
    import weaviate

    # Connects to Weaviate Cloud, or point this at a self-hosted instance.
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url="YOUR_CLUSTER_URL",
        auth_credentials=weaviate.auth.AuthApiKey("YOUR_API_KEY"),
    )

    documents = client.collections.get("Documents")

    # Add vectors -- Weaviate can generate embeddings for you automatically,
    # or you can supply your own, same as the other two examples.
    documents.data.insert({"title": "What is RAG"}, vector=[0.1, 0.2, ...])

    # Search -- this example shows hybrid search: part keyword, part vector.
    results = documents.query.hybrid(query="what is retrieval augmented generation", limit=3)
    '''
    print("--- Weaviate ---")
    print(example_code)


def when_to_use_which():
    print("--- Quick guide: which one should you reach for? ---\n")
    print("  Just prototyping, want zero setup:      Chroma (runs in-process, no server)")
    print("  Want managed, don't want to run servers: Pinecone")
    print("  Need massive scale, want full control:   Milvus (self-hosted)")
    print("  Want vector + keyword search combined:   Weaviate")
    print("  Building a custom search engine:         FAISS (as a library, not a full DB)")


def main():
    print("=== Real Vector Database Examples ===")
    print("(This file shows code structure only -- nothing here actually runs\n"
          " or connects to anything. No API key needed to read it.)\n")

    pinecone_example()
    milvus_example()
    weaviate_example()
    when_to_use_which()


if __name__ == "__main__":
    main()
