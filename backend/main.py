from fastapi import FastAPI, UploadFile, File
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from typing import Optional, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import create_agent
from tool import tools 
import uuid
import os

from dotenv import load_dotenv
load_dotenv()


# -----------------------------
# Initialize FastAPI
# -----------------------------

app = FastAPI(title="FALCON Backend")

# -----------------------------
# Initialize LLM + Agent
# -----------------------------

llm = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url="http://localhost:11434",
    temperature=0,
)

# If you have tools, import them
llm_with_tools = llm.bind_tools(tools)
agent = create_agent(llm_with_tools, tools)

# -----------------------------
# In-Memory Chat Store
# -----------------------------

chat_sessions: Dict[str, List[Dict]] = {}

# -----------------------------
# Request Models
# -----------------------------

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    character: str
    query: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


# -----------------------------
# Character Prompts
# -----------------------------

def get_prompt(character: str) -> str:
    prompts = {
        "💭General Chat": "You are FALCON AI assistant.",
        "🤖AI Tutor": "You are an AI tutor who explains concepts clearly.",
        "💪Fitness Coach": "You are a professional fitness coach.",
        "🎓Career Advisor": "You are a career advisor.",
        "👨‍🔬Dr. APJ Abdul Kalam": "Respond like Dr. APJ Abdul Kalam.",
        "👴🏻Mahatma Gandhi": "Respond like Mahatma Gandhi.",
    }
    return prompts.get(character, "You are FALCON AI assistant.")


# -----------------------------
# Chat Endpoint
# -----------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    # Create new session if not provided
    if not request.session_id:
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = []
    else:
        session_id = request.session_id
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

    history = chat_sessions[session_id]

    # Build messages
    messages = [SystemMessage(content=get_prompt(request.character))]

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=request.query))

    # Call agent
    result = agent.invoke({"messages": messages})
    final_response = result["messages"][-1].content

    # Save history
    history.append({"role": "user", "content": request.query})
    history.append({"role": "assistant", "content": final_response})

    return ChatResponse(
        session_id=session_id,
        response=final_response
    )