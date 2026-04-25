from sqlmodel import Field, SQLModel, Relationship
from typing import Optional
from datetime import datetime, date, time
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    moderator = "moderator"


class AssetCategory(str, Enum):
    baler = "baler"
    conveyor = "conveyor"
    bobcat = "bobcat"
    forklift = "forklift"
    scale = "scale"


class AssetOwnership(str, Enum):
    owned = "owned"
    rented = "rented"
    leased = "leased"


class AssetStatus(str, Enum):
    operational = "operational"
    maintenance = "maintenance"
    disposed = "disposed"
    out_of_service = "out_of_service"


class AssetSubStatus(str, Enum):
    watch_list = "watch_list"
    limited_duty = "limited_duty"
    pending_inspection = "pending_inspection"
    in_repair = "in_repair"
    awaiting_parts = "awaiting_parts"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    firstname: str
    lastname: str
    role: UserRole = Field(default=UserRole.user)
    email: str = Field(unique=True)
    password: str
    active: bool = Field(default=True)
    first_login: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)


class Asset(SQLModel, table=True):
    asset_id: Optional[str] = Field(primary_key=True, default=None)
    manufacturer: str
    model_no: Optional[str] = Field(default=None)
    yr: Optional[int] = Field(default=None)
    serial_no: Optional[str] = Field(default=None)
    category: AssetCategory = Field(default=None)
    depot: str  # Relationship here
    owned: AssetOwnership = Field(default=AssetOwnership.owned)
    date_in_service: Optional[date] = Field(default=None)
    status: AssetStatus = Field(default=AssetStatus.operational)
    sub_status: Optional[AssetSubStatus] = Field(default=None)
