from typing import Optional
from uuid import UUID

from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.retrievers import BaseRetriever
from langchain_groq import ChatGroq

from api.schemas import AnswerResponse, SourceChunk
from core.config import get_settings
from services.session_memory import session_memory
from services.vector_store import vector_store_manager

_CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Given the chat history and a follow-up question, rephrase the follow-up "
        "to be a standalone question. If there is no chat history, return the question as-is.",
    ),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

_QA_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "Answer using ONLY the context below. "
        "Cite sources as [filename:page] when referencing specific content. "
        "If the context is insufficient, say so clearly.\n\n{context}",
    ),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


class _ManagerRetriever(BaseRetriever):
    doc_id: Optional[str] = None
    k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        results = vector_store_manager.retrieve(query, k=self.k, doc_id=self.doc_id)
        docs = []
        for doc, score in results:
            doc.metadata["_score"] = score
            docs.append(doc)
        return docs


def get_answer(
    question: str,
    session_id: UUID,
    doc_id: Optional[UUID] = None,
) -> AnswerResponse:
    settings = get_settings()
    llm = ChatGroq(
        model=settings.GROQ_CHAT_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

    turns = session_memory.get_turns(session_id)
    chat_history = [
        msg
        for turn in turns
        for msg in (HumanMessage(content=turn["question"]), AIMessage(content=turn["answer"]))
    ]

    # Condense follow-up into a standalone question only when history exists
    if chat_history:
        retrieval_question = (_CONDENSE_PROMPT | llm | StrOutputParser()).invoke(
            {"input": question, "chat_history": chat_history}
        )
    else:
        retrieval_question = question

    retriever = _ManagerRetriever(
        doc_id=str(doc_id) if doc_id else None,
        k=settings.RETRIEVAL_K,
    )
    docs = retriever.invoke(retrieval_question)

    context = "\n\n".join(
        f"[{doc.metadata.get('filename', '')}:{doc.metadata.get('page_number', '')}]\n{doc.page_content}"
        for doc in docs
    )

    answer_text = (_QA_PROMPT | llm | StrOutputParser()).invoke(
        {"input": question, "chat_history": chat_history, "context": context}
    )

    sources = [
        SourceChunk(
            doc_id=doc.metadata.get("doc_id", ""),
            filename=doc.metadata.get("filename", ""),
            page_number=doc.metadata.get("page_number"),
            text=doc.page_content[:300],
            score=float(doc.metadata.get("_score", 0.0)),
        )
        for doc in docs
    ]

    session_memory.add_turn(session_id, question, answer_text)
    return AnswerResponse(answer=answer_text, sources=sources, session_id=session_id)
