from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
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
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1
    )

def load_groq_fast():
    return ChatGroq(
        model="llama3-70b-8192",
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2
    )

def load_gemini():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.3
    )

def load_gemini_image():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-image",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2
    )

load_groq()
load_openai()
load_groq_fast()
load_gemini()
load_gemini_image()