from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq.chat_models import ChatGroq
from langchain_ollama import ChatOllama
# from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
import os
from dotenv import load_dotenv
load_dotenv()



gemini_3_6_flash_model = ChatGoogleGenerativeAI(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-3.6-flash", temperature=0.6)

gemini_3_5_flash_model = ChatGoogleGenerativeAI(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-3.5-flash", temperature=0.6)

# groq_openai_120b = ChatGroq(model="openai/gpt-oss-120b", temperature=1.0, api_key=os.getenv("GROQ_API_KEY"))

# llama_3_3_70b_versatile = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=os.getenv("GROQ_API_KEY"))