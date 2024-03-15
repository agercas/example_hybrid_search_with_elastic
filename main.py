from typing import List

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.api.chat import Chat
from src.api.search import Search
from src.models import ChatQuestion, Document, DocumentID, SearchQuery

app = FastAPI()
es = Search()
chat = Chat()

# Set up template directory
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/documents/", response_model=DocumentID)
async def add_document(document: Document) -> DocumentID:
    return es.insert_document(document)


@app.get("/documents/{doc_id}", response_model=Document)
async def get_document(doc_id: str) -> Document:
    document = es.retrieve_document(doc_id)
    if document:
        return document
    raise HTTPException(status_code=404, detail="Document not found")


# TODO: fix response model type
@app.post("/search/", response_model=List[Document])
async def search_documents(query: SearchQuery):
    results = es.search(
        query={
            "bool": {
                "must": {"multi_match": {"query": query.query, "fields": ["name", "summary", "content"], "boost": 0.7}}
            }
        },
        knn={
            "field": "embedding",
            "query_vector": es.get_embedding(query.query),
            "num_candidates": 50,
            "k": query.top_k,
            "boost": 0.3,
        },
        # rank={
        #     'rrf': {}
        # },
        size=query.top_k,
    )

    return results["hits"]["hits"]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@app.post("/", response_class=HTMLResponse)
async def handle_search(request: Request, query: str = Form(""), from_: int = Form(0)):
    results = es.search(
        query={
            "bool": {"must": {"multi_match": {"query": query, "fields": ["name", "summary", "content"], "boost": 0.7}}}
        },
        knn={
            "field": "embedding",
            "query_vector": es.get_embedding(query),
            "num_candidates": 50,
            "k": 10,
            "boost": 0.3,
        },
        # rank={
        #     'rrf': {}
        # },
        size=5,
        from_=from_,
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "query": query,
            "results": results["hits"]["hits"],
            "from_": from_,
            "total": results["hits"]["total"]["value"],
        },
    )


@app.get("/document/{doc_id}", response_class=HTMLResponse)
async def show_document(request: Request, doc_id: str):
    document = es.retrieve_document(doc_id)
    title = document.name
    paragraphs = document.content.split("\n")
    print("request: ", request)
    return templates.TemplateResponse("document.html", {"request": request, "title": title, "paragraphs": paragraphs})


@app.get("/chat/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request, "answer": None})


@app.post("/chat/", response_class=HTMLResponse)
async def handle_chat_message(request: Request, question: str = Form(...)):
    documents = await search_documents(SearchQuery(query=question, top_k=1))

    chat_question = ChatQuestion(question=question)

    try:
        answer = chat.get_answer_with_documents(chat_question, documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse("chat.html", {"request": request, "answer": answer})
