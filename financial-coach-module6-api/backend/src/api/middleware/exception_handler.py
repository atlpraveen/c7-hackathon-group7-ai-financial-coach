from fastapi.responses import JSONResponse

def api_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={'error': str(exc)})
