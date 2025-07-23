import os
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
# from langchain_azure import ChatAzure
# from langchain_ollama import ChatOllama
# from langchain_anthropic import ChatAnthropic
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_huggingface import HuggingFacePipeline, ChatHuggingFace


# LLM Models
# OpenAI
openai_4o = ChatOpenAI(model="gpt-4o", temperature=0)
openai_o3_mini = ChatOpenAI(model="o3-mini")
# openai_o3_mini = init_chat_model(
#     model="o3-mini",
#     temperature=0,
#     base_url="https://api.openai.com/v1",
#     api_key=os.getenv("OPENAI_API_KEY")
# )


# # Azure
# azure_gpt_4o = ChatAzure(model="gpt-4o", temperature=0)

# # Ollama
# ollama_llama3_8b = ChatOllama(model="llama3.8b", temperature=0)

# # Anthropic
# anthropic_claude_3_5_sonnet = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

# # Google
# google_gemini_1_5_flash = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# # Hugging Face
# hf_qwen_vl_pipeline = HuggingFacePipeline.from_model_id(
#     model_id="Qwen/Qwen2.5-VL-7B-Instruct",
#     task="image-to-text",
#     pipeline_kwargs={
#         "max_new_tokens": 100,
#         "temperature": 0,
#     }
# )
# huggingface_qwen_vl = ChatHuggingFace(llm=hf_qwen_vl_pipeline)





# Static Analysis
STATIC_ANALYSIS_ANALYST_LLM = openai_o3_mini
STATIC_ANALYSIS_TRIAGE_LLM = openai_o3_mini
STATIC_ANALYSIS_TECHNICIAN_LLM = openai_o3_mini
STATIC_ANALYSIS_STRATEGIC_REVIEW_LLM = openai_o3_mini


# Visual Analysis
VISUAL_ANALYSIS_ANALYST_LLM = openai_4o
# VISUAL_ANALYSIS_ANALYST_LLM = huggingface_qwen_vl


