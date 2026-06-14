from fastapi import APIRouter
router = APIRouter()

@router.post('/analyze')
def analyze_debt():
    return {'result':'debt analysis'}
