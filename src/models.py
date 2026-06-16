from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq.chat_models import ChatGroq
from langchain_ollama import ChatOllama
# from langchain_openai import ChatOpenAI
from langchain_openrouter import ChatOpenRouter
import os
from dotenv import load_dotenv
load_dotenv()



gemini_3_5_flash_model = ChatGoogleGenerativeAI(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-3.5-flash", temperature=0.6)

gemini_3_1_flash_model = ChatGoogleGenerativeAI(api_key=os.getenv("GEMINI_API_KEY"), model="gemini-3-flash-preview", temperature=0.1)

# groq_openai_120b = ChatGroq(model="openai/gpt-oss-120b", temperature=1.0, api_key=os.getenv("GROQ_API_KEY"))

# llama_3_3_70b_versatile = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=os.getenv("GROQ_API_KEY"))


# openrouter_openai_qwen3 = ChatOpenRouter(
#     api_key=os.getenv("OPENROUTER_API_KEY"),
#     model= "qwen/qwen3-next-80b-a3b-instruct:free",
#     temperature=0.1,
# )

# ollama_allam_7b = ChatOllama(
#     model="iKhalid/ALLaM:7b", #"qwen3:8b", # أو "gemma2:9b"
#     temperature=0.1, 
#     num_ctx=4096,    # تأكد أن المقال لا يتجاوز هذا الحد
#     num_predict=2048,
#     num_gpu=99,
#     keep_alive="0m"
# )