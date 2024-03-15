from typing import List

from langchain_community.llms import Ollama

from src.models import ChatQuestion, Document


def _generate_prompt(question: ChatQuestion, documents: List[Document]) -> str:
    prompt = "Use the following documents to answer the user's question.\n"
    prompt += (
        "Each passage has a NAME which is the title of the document. After your answer, "
        "leave a blank line and then give the source name of the passages you answered from. "
        "Put them in a comma separated list, prefixed with SOURCES:.\n\n"
    )

    for document in documents:
        doc = document["_source"]
        prompt += "---\n"
        prompt += "NAME: {}\n".format(doc["name"])
        prompt += "DOCUMENT:\n{}\n".format(doc["content"])
        prompt += "---\n\n"

    prompt += "Question: {}\nResponse:".format(question.question)
    return prompt


class Chat:
    def __init__(self, model_name: str = "gemma:2b"):
        self.llm = Ollama(model=model_name)

    def get_answer(self, question: ChatQuestion) -> str:
        response = self.llm.invoke(question.question)
        return response

    def get_answer_with_documents(self, question: ChatQuestion, documents: List[Document]) -> str:
        prompt = _generate_prompt(question, documents)
        response = self.llm.invoke(prompt)
        return response
