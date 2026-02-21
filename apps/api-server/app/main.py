from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import generate, slides, qna, tts

app = FastAPI(title="GyML AI Teacher API")

# Configure CORS so the Next.js frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(slides.router, prefix="/api/slides", tags=["slides"])
app.include_router(qna.router, prefix="/api/qna", tags=["qna"])
app.include_router(tts.router, prefix="/api/tts", tags=["tts"])

@app.get("/")
def read_root():
    return {"message": "GyML AI Teacher API is running"}
