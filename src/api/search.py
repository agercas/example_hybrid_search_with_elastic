import json
import os
from pprint import pprint
from typing import List, Optional

from dotenv import load_dotenv
from elasticsearch import Elasticsearch, NotFoundError
from sentence_transformers import SentenceTransformer

from src.models import Document, DocumentID

load_dotenv()
current_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.join(current_dir, "..", "..")

ELASTIC_URL = os.environ["ELASTIC_URL"]
ELASTIC_USERNAME = os.environ["ELASTIC_USERNAME"]
ELASTIC_PASSWORD = os.environ["ELASTIC_PASSWORD"]
ELASTIC_HTTP_CA_CRT = os.path.join(root_dir, os.environ["ELASTIC_HTTP_CA_CRT"])

SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"
SEARCH_INDEX = "documents"


class Search:
    def __init__(self):
        self.model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        self.es = Elasticsearch(
            hosts=[ELASTIC_URL],
            basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
            verify_certs=True,
            ca_certs=ELASTIC_HTTP_CA_CRT,
        )
        client_info = self.es.info()
        print("Connected to Elasticsearch!")
        pprint(client_info.body)

    def get_embedding(self, text: str):
        return self.model.encode(text)

    def create_index(self):
        self.es.indices.delete(index=SEARCH_INDEX, ignore_unavailable=True)
        self.es.indices.create(
            index=SEARCH_INDEX,
            mappings={
                "properties": {
                    "embedding": {
                        "type": "dense_vector",
                    }
                }
            },
        )

    def reindex(self, file_path: str) -> dict:
        """
        Reindexes the documents by creating a new index and inserting documents from a specified JSON file.
        """
        self.create_index()
        try:
            with open(file_path, "rt") as f:
                documents = json.load(f)
            return self.insert_documents(documents)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return {"error": "File not found"}
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}")
            return {"error": "Error decoding JSON"}

    def insert_document(self, document: Document) -> DocumentID:
        # TODO: split content into chunks instead of taking the summary
        embedding = self.get_embedding(document.get("summary", ""))
        response = self.es.index(
            index=SEARCH_INDEX,
            document={
                **document,
                "embedding": embedding,
            },
        )
        return DocumentID(id=response["_id"])

    def insert_documents(self, documents: List[dict]) -> dict:
        operations = []
        for document in documents:
            operations.append({"index": {"_index": SEARCH_INDEX}})
            operations.append(
                {
                    **document,
                    "embedding": self.get_embedding(document["summary"]),
                }
            )
        return self.es.bulk(operations=operations)

    def search(self, **query_args):
        return self.es.search(index=SEARCH_INDEX, **query_args)

    def retrieve_document(self, doc_id: str) -> Optional[Document]:
        try:
            doc = self.es.get(index=SEARCH_INDEX, id=doc_id)
            return Document(**doc["_source"], id=doc["_id"])
        except NotFoundError:
            return None
        except Exception as e:
            print(f"Error retrieving document: {e}")
            return None
