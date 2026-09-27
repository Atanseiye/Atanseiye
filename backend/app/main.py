from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .routes.api import router
from .routes.onboarding import router as onboarding_router

app=FastAPI(title="AccessFlow AI",description="Multilingual accessibility SDK and safe banking demo",version="0.9.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["GET","POST","PUT"],allow_headers=["*"])
app.include_router(router)
app.include_router(onboarding_router)
STATIC=Path(__file__).parent/"static"; app.mount("/static",StaticFiles(directory=STATIC),name="static")
@app.get("/health")
def health(): return {"status":"ok","service":"accessflow","version":"0.9.0"}
@app.get("/")
def demo(): return FileResponse(STATIC/"index.html")
@app.get("/admin")
def admin(): return FileResponse(STATIC/"admin.html")

@app.get("/register")
def register(): return FileResponse(STATIC/"register.html")

@app.get("/pitch", include_in_schema=False)
def pitch():
    return FileResponse(STATIC/"pitch.pdf", media_type="application/pdf", headers={"Content-Disposition": 'inline; filename="AccessFlow_AI_Zecathon_6_Pitch_Deck.pdf"', "Cache-Control": "public, max-age=3600"})
