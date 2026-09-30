from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from legalEaseAPI.routes import router

app = FastAPI(title="LegalEase - AI Legal Document Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your Streamlit URL when deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Welcome to LegalEase AI Legal Document Generator API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
