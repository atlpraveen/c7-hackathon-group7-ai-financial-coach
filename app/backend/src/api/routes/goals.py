"""Financial goal tracking: CRUD + progress/projection analytics."""
from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import UserContext, get_context
from src.api.schemas import GoalInput, GoalUpdate
from src.db import repository as repo
from src.db.models import Goal
from src.services.goals import summarize_goals

router = APIRouter()


def _goal_dict(g: Goal) -> dict:
    return {
        "id": g.id,
        "name": g.name,
        "category": g.category,
        "target_amount": g.target_amount,
        "current_amount": g.current_amount,
        "monthly_contribution": g.monthly_contribution,
        "target_months": g.target_months,
        "annual_return": g.annual_return,
    }


@router.get("")
def list_goals(ctx: UserContext = Depends(get_context)):
    goals = [_goal_dict(g) for g in repo.list_goals(ctx.db, ctx.user_id)]
    return summarize_goals(goals)


@router.post("")
def create_goal(body: GoalInput, ctx: UserContext = Depends(get_context)):
    goal = repo.create_goal(ctx.db, ctx.user_id, **body.model_dump())
    return summarize_goals([_goal_dict(g) for g in repo.list_goals(ctx.db, ctx.user_id)]) | {"created_id": goal.id}


@router.put("/{goal_id}")
def update_goal(goal_id: int, body: GoalUpdate, ctx: UserContext = Depends(get_context)):
    goal = repo.update_goal(ctx.db, ctx.user_id, goal_id, **body.model_dump())
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    return summarize_goals([_goal_dict(g) for g in repo.list_goals(ctx.db, ctx.user_id)])


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, ctx: UserContext = Depends(get_context)):
    if not repo.delete_goal(ctx.db, ctx.user_id, goal_id):
        raise HTTPException(status_code=404, detail="Goal not found.")
    return summarize_goals([_goal_dict(g) for g in repo.list_goals(ctx.db, ctx.user_id)])
