from fastapi import APIRouter
router = APIRouter()

@router.post('/plan')
def savings_plan():
    return {'result':'savings plan'}
