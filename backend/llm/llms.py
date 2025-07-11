import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in .env file")


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
)

llm_creative = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.5,
)


if __name__ == '__main__':
    print(llm_creative.invoke("What is the capital of France?"))
