from fastapi import APIRouter, UploadFile
router = APIRouter()

@router.post('/upload')
async def upload_document(file: UploadFile):
    return {'filename': file.filename}
