import asyncio
from functools import lru_cache
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from agent.flashrank_reranker import rerank
from agent.guardrails_service import MedicalGuardrails
from agent.llm import get_llm
from retrieval.qdrant_retriever import QdrantHybridRetriever, RetrievedDocument
from tools.alert_system import generate_alerts
from tools.drug_interaction_tool import check_drug_interaction
from tools.health_predictor import predict_health_risk


class MedicalState(TypedDict, total=False):
    query: str
    role: str
    history: list[dict[str, str]]
    docs: list[RetrievedDocument]
    answer: str
    sources: list[dict]
    guardrail_action: str


guardrails = MedicalGuardrails()

@lru_cache
def get_retriever() -> QdrantHybridRetriever:
    return QdrantHybridRetriever()


def _tool_response(query: str) -> str | None:
    normalized = query.lower()
    if "interaction" in normalized:
        words = [word for word in normalized.replace("?", "").split() if word.isalpha()]
        ignored = {"drug", "interaction", "between", "and", "with", "check", "for"}
        medicines = [word for word in words if word not in ignored]
        if len(medicines) >= 2:
            return check_drug_interaction(medicines[-2], medicines[-1])
    if "blood pressure" in normalized or "bp" in normalized or "risk" in normalized:
        numbers = [int(value) for value in __import__("re").findall(r"\d+", normalized)]
        if numbers:
            age, bp = (numbers[0], numbers[1]) if len(numbers) > 1 else (30, numbers[0])
            return f"{predict_health_risk(age, bp)}\n\nAlerts:\n" + "\n".join(generate_alerts(bp))
    return None


async def input_guard(state: MedicalState) -> MedicalState:
    result = await guardrails.validate_input(state["query"])
    if result.action != "allow":
        return {"answer": result.message or "Request blocked.", "guardrail_action": result.action, "sources": []}
    return {"guardrail_action": "allow"}


async def retrieve_documents(state: MedicalState) -> MedicalState:
    tool_answer = _tool_response(state["query"])
    if tool_answer:
        return {"answer": tool_answer, "sources": []}
    docs = await asyncio.to_thread(get_retriever().retrieve, state["query"], 12)
    return {"docs": await asyncio.to_thread(rerank, state["query"], docs, 5)}


async def generate_answer(state: MedicalState) -> MedicalState:
    if state.get("answer"):
        return {"answer": guardrails.validate_output(state["answer"]), "sources": state.get("sources", [])}
    documents = state.get("docs", [])
    if not documents:
        return {
            "answer": guardrails.validate_output(
                "I could not find a relevant reference in the curated medical knowledge base for that question."
            ),
            "sources": [],
        }
    context = "\n\n".join(
        f"[{index + 1}] {doc.name} — {doc.section}: {doc.text}" for index, doc in enumerate(documents)
    )
    history = "\n".join(
        f"User: {turn.get('user', '')}\nAssistant: {turn.get('assistant', '')}" for turn in state.get("history", [])[-6:]
    )
    system = (
        "You are MedAssist, a careful medical information assistant. Answer only from the supplied sources. "
        "Do not diagnose, prescribe, or invent facts. State uncertainty plainly. Use concise Markdown with source markers [1], [2]. "
        f"The user role is {state.get('role', 'user')}."
    )
    user_prompt = f"Conversation context:\n{history or 'None'}\n\nSources:\n{context}\n\nQuestion: {state['query']}"
    response = await get_llm().ainvoke([SystemMessage(content=system), HumanMessage(content=user_prompt)])
    return {
        "answer": guardrails.validate_output(str(response.content)),
        "sources": [document.citation() for document in documents],
    }


def route_after_guard(state: MedicalState) -> str:
    return "end" if state.get("guardrail_action") != "allow" else "retrieve"


graph_builder = StateGraph(MedicalState)
graph_builder.add_node("input_guard", input_guard)
graph_builder.add_node("retrieve", retrieve_documents)
graph_builder.add_node("generate", generate_answer)
graph_builder.add_edge(START, "input_guard")
graph_builder.add_conditional_edges("input_guard", route_after_guard, {"end": END, "retrieve": "retrieve"})
graph_builder.add_edge("retrieve", "generate")
graph_builder.add_edge("generate", END)
medical_graph = graph_builder.compile()


async def run_medical_workflow(query: str, role: str, history: list[dict[str, str]] | None = None) -> dict:
    result = await medical_graph.ainvoke({"query": query, "role": role, "history": history or []})
    return {
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "guardrail_action": result.get("guardrail_action", "allow"),
    }
