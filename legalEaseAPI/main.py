"""FastAPI entry point.  Run from the project root:

    uvicorn legalEaseAPI.main:app --reload
"""
import logging

from fastapi import FastAPI

import config
from legalEaseAPI.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="LegalEase - AI Legal Document Generator", version="1.0.0")

# Include API routes
app.include_router(router)


@app.get("/")
def home():
    return {"message": "Welcome to LegalEase AI Legal Document Generator API"}


# Run directly with:  python -m legalEaseAPI.main
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("legalEaseAPI.main:app", host=config.API_HOST, port=config.API_PORT, reload=True)
