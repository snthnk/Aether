import os
from dotenv import load_dotenv

load_dotenv()

model = os.getenv("MODEL")

if model in ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash-lite"]:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from google.generativeai.types import HarmCategory, HarmBlockThreshold

    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY not found in .env file")

    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=0.2,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    )

    llm_creative = ChatGoogleGenerativeAI(
        model=model,
        temperature=0.5,
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    )

elif model in ["gemma3:27b"]:
    from langchain_ollama import ChatOllama

    llm = ChatOllama(model=model, base_url=os.getenv("BASE_URL"), temperature=0.2)
    llm_creative = ChatOllama(model=model, base_url=os.getenv("BASE_URL"), temperature=0.5)

elif model in ["gpt-4o-mini",
               "deepseek-v3",
               "grok-3-mini-high",
               "phi-4",
               "gpt-4.1",
               "gpt-4.5",
               "qwen-2.5-coder-32b",
               "o4-mini",
               "o4-mini-high"]:
    from llm.gpt4free import GPT4Free

    llm = GPT4Free(model=model, temperature=0.2)
    llm_creative = GPT4Free(model=model, temperature=0.5)

else:
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=model,
        temperature=0.2,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    llm_creative = ChatOpenAI(
        model=model,
        temperature=0.5,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

if __name__ == '__main__':
    print(llm.invoke("What is the capital of France?"))
