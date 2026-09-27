from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .routes.api import router

app=FastAPI(title="AccessFlow AI",description="Multilingual accessibility SDK and safe banking demo",version="0.8.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["GET","POST","PUT"],allow_headers=["*"])
app.include_router(router)
STATIC=Path(__file__).parent/"static"; app.mount("/static",StaticFiles(directory=STATIC),name="static")
@app.get("/health")
def health(): return {"status":"ok","service":"accessflow","version":"0.8.0"}
@app.get("/")
def demo(): return FileResponse(STATIC/"index.html")
@app.get("/admin")
def admin(): return FileResponse(STATIC/"admin.html")
