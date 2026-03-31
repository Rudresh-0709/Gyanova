import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Serve audio files so the frontend player can fetch narration segments
# Placed in .persistent_data to avoid triggering Next.js reloads when new audio is generated
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_ROOT = ROOT_DIR / ".persistent_data"
audio_dir = DATA_ROOT / "audio_output"
os.makedirs(audio_dir, exist_ok=True)

if os.path.isdir(audio_dir):
    app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")


cleanup_loop_task = None


async def _audio_cleanup_loop():
    """Periodically clean up expired audio files from completed/closed lessons."""
    while True:
        try:
            summary = generate.cleanup_expired_task_audio()
            if summary.get("deleted_files", 0) > 0:
                print(
                    f"🧹 Audio cleanup: deleted {summary['deleted_files']} files "
                    f"across {summary['cleaned_tasks']} task(s)."
                )
        except Exception as e:
            print(f"⚠️ Audio cleanup loop error: {e}")

        # Sweep every 5 minutes
        await asyncio.sleep(300)


@app.on_event("startup")
async def _startup_audio_cleanup_loop():
    global cleanup_loop_task
    # Initial sweep on boot
    try:
        generate.cleanup_expired_task_audio()
    except Exception as e:
        print(f"⚠️ Initial audio cleanup failed: {e}")

    cleanup_loop_task = asyncio.create_task(_audio_cleanup_loop())


@app.on_event("shutdown")
async def _shutdown_audio_cleanup_loop():
    global cleanup_loop_task
    if cleanup_loop_task:
        cleanup_loop_task.cancel()
        try:
            await cleanup_loop_task
        except asyncio.CancelledError:
            pass


@app.get("/")
def read_root():
    return {"message": "GyML AI Teacher API is running"}
