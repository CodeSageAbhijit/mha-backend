from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class TodoPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TodoStatusEnum(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TodoCreate(BaseModel):
    """Schema for creating a new TODO"""
    title: str
    description: Optional[str] = None
    priority: TodoPriorityEnum = TodoPriorityEnum.MEDIUM
    status: TodoStatusEnum = TodoStatusEnum.TODO
    due_date: Optional[datetime] = None
    assignee_id: Optional[str] = None
    user_id: str  # Creator/owner


class TodoUpdate(BaseModel):
    """Schema for updating a TODO"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TodoPriorityEnum] = None
    status: Optional[TodoStatusEnum] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[str] = None


class TodoResponse(BaseModel):
    """Schema for TODO response"""
    id: str
    title: str
    description: Optional[str]
    priority: TodoPriorityEnum
    status: TodoStatusEnum
    due_date: Optional[datetime]
    assignee_id: Optional[str]
    user_id: str
    created_at: datetime
    updated_at: datetime


class TodoList(BaseModel):
    """Schema for TODO list response"""
    todos: list
    total: int
    status: str
    message: str
