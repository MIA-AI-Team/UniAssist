"""
Handles task creation and retrieval:
    - create_task()   — professor/TA creates a task with type-specific details
    - get_task()      — get a single task by id
    - list_tasks()    — list tasks filtered by cohort/major for students
"""
from __future__ import annotations


from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tasks import Task, TaskLabDetails, TaskAssignmentDetails, TaskProjectDetails
from backend.models.enums import TaskType
from  backend.repository import _get_task, get_file_by_id
from backend.repository.embedding_repository import link_embeddings_to_task



async def create_task(data: dict, created_by: int,  db: AsyncSession) -> Task:
    """
    Create a TASKS row + the matching type-specific details row.       
    Raises:
        HTTPException 422 — missing required fields for task type
        HTTPException 400 — invalid task type
    """

    task_type = data.get("type")
    if task_type not in [t.value for t in TaskType]:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {task_type}. Must be lab | assignment | project")
    reference_file_id = data.get("reference_file_id")

    # Convert 0 or empty values from Swagger/forms to None
    if reference_file_id in (0, "", None):
        reference_file_id = None
    else:
        # Must await async database calls!
        file_record = await get_file_by_id(reference_file_id, db)
        if not file_record:
            raise HTTPException(
                status_code=404,
                detail=f"Reference file with ID {reference_file_id} not found."
            )
    

    task = Task(
        type=TaskType(task_type),
        title=data["title"],
        description=data.get("description", ""),
        due_date=data["due_date"],
        target_cohort_year=data["target_cohort_year"],
        target_major=data.get("target_major"),
        created_by=created_by,
        reference_file_id=data.get("reference_file_id"),

    )
    db.add(task)
    await db.flush()  # get task.id


    if task_type == "lab":
        db.add(TaskLabDetails(
            task_id=task.id,
            scheduled_date=data["scheduled_date"],
        ))

    elif task_type == "assignment":
        db.add(TaskAssignmentDetails(
            task_id=task.id,
            allowed_file_types=data.get("allowed_file_types", ["pdf", "zip"]),
            allow_late=data.get("allow_late", False),
        ))

    elif task_type == "project":
        db.add(TaskProjectDetails(
            task_id=task.id,
            default_repo_provider=data.get("default_repo_provider", "github"),
            require_team=data.get("require_team", True),
        ))
    if reference_file_id:
        await link_embeddings_to_task(reference_file_id, task.id, db)
    await db.commit()
    await db.refresh(task)

    return task



async def get_task(task_id: int, db: AsyncSession) -> Task:
    """
    Raises:
        HTTPException 404 — task not found
    """
    task = await _get_task(task_id, db)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
    return task


