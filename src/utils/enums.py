import enum

class Status(enum.Enum):
    Pending = "pending"
    Rejected = "rejected"
    Approved = "approved"

class Type(enum.Enum):
    Maturita = "maturita"
    Task = "task"

class Role(enum.Enum):
    Student = "student"
    Teacher = "teacher"
    Admin = "admin"