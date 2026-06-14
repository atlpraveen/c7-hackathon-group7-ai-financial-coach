from fastapi import APIRouter
router = APIRouter()

@router.post('/recommend')
def recommend():
    return {'result':'investment recommendation'}
