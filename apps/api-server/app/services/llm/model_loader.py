from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

def load_openai():
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.5
    )

def load_groq():
    return ChatGroq(
        model="lava-1.5",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2
    )

def load_groq_fast():
    return ChatGroq(
        model="llama3-70b-8192",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2
    )

load_groq()
load_openai()