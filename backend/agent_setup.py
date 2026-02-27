from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from tool import tools  
from dotenv import load_dotenv
load_dotenv()


# Initialize LLM
llm = ChatOllama(
    model="kimi-k2.5:cloud",
    base_url="http://localhost:11434",
    temperature=0
)

# Bind tools
llm_with_tools = llm.bind_tools(tools)

# Create agent
agent = create_agent(llm_with_tools, tools)