from fastapi import FastAPI

app = FastAPI(title="MoneyNarrator API")


@app.get("/")
def read_root():
    """Health-check / hello-world endpoint.

    If you can see this response, the FastAPI server is running correctly.
    """
    return {"message": "MoneyNarrator API is running"}
