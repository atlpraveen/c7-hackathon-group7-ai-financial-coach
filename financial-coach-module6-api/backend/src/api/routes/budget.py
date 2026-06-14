from fastapi import APIRouter
router = APIRouter()

@router.post('/optimize')
def optimize_budget():
    return {'result':'budget optimization'}
