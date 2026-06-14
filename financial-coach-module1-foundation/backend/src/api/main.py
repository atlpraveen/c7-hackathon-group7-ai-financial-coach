from fastapi import FastAPI

app = FastAPI(title="Financial Coach API")

@app.get("/health")
async def health():
    return {"status": "healthy"}
