from sqlalchemy import or_, func, and_, outerjoin
from src.models.User import User
from src.models.Specialization import Specialization
from src.models.Class import Class
from src.models.Task import Task
from src.models.Team import Team
from src.utils.enums import Role, Type
from src.models.User_Class import User_Class
from src.models.User_Team import User_Team

def user_paging(searchQuery, amountForPaging, pageNumber, specialSearch = None, typeOfSpecialSearch = None):
    words = [w.strip().lower() for w in searchQuery.split() if w.strip()]

    conditions = []
    specialConditions = []
    for word in words:
        like_pattern = f"%{word}%"
        conditions.append(
            or_(
                func.lower(User.name).like(like_pattern),
                func.lower(User.surname).like(like_pattern),
                func.lower(User.email).like(like_pattern),
                func.lower(User.abbreviation).like(like_pattern),
            )
        )

    if typeOfSpecialSearch == "noClass":
            return User.query.outerjoin(User_Class, User.id == User_Class.idUser).filter(User.role == Role.Student).filter(User_Class.idUser == None).filter(and_(*conditions)).offset(amountForPaging * pageNumber).limit(amountForPaging), User.query.outerjoin(User_Class, User.id == User_Class.idUser).filter(User.role == Role.Student).filter(User_Class.idUser == None).filter(and_(*conditions)).count()

    if specialSearch:
        if not typeOfSpecialSearch:
            return False
        
        if typeOfSpecialSearch == "createdAt":
            specialConditions.append(User.createdAt == specialSearch)
        if typeOfSpecialSearch == "role":
            specialConditions.append(User.role == specialSearch)
        if typeOfSpecialSearch == "updatedAt":
            specialConditions.append(User.updatedAt == specialSearch)
    return User.query.filter(and_(*conditions, *specialConditions)).offset(amountForPaging * pageNumber).limit(amountForPaging), User.query.filter(and_(*conditions, *specialConditions)).count()

def specialization_paging(searchQuery, amountForPaging, pageNumber):
    words = [w.strip().lower() for w in searchQuery.split() if w.strip()]

    conditions = []
    for word in words:
        like_pattern = f"%{word}%"
        conditions.append(
            or_(
                func.lower(Specialization.name).like(like_pattern),
                func.lower(Specialization.abbreviation).like(like_pattern),
            )
        )

    return Specialization.query.filter(and_(*conditions)).offset(amountForPaging * pageNumber).limit(amountForPaging), Specialization.query.filter(and_(*conditions)).count()

def class_paging(searchQuery, amountForPaging, pageNumber):
    words = [w.strip().lower() for w in searchQuery.split() if w.strip()]

    conditions = []
    for word in words:
        like_pattern = f"%{word}%"
        conditions.append(
            or_(
                func.lower(Class.name).like(like_pattern)
            )
        )

    return Class.query.filter(and_(*conditions)).offset(amountForPaging * pageNumber).limit(amountForPaging), Class.query.filter(and_(*conditions)).count()

def task_paging(searchQuery, amountForPaging, pageNumber, specialSearch = None, typeOfSpecialSearch = None):
    words = [w.strip().lower() for w in searchQuery.split() if w.strip()]

    conditions = []
    specialConditions = []
    for word in words:
        like_pattern = f"%{word}%"
        conditions.append(
            or_(
                func.lower(Task.name).like(like_pattern),
                func.lower(Task.points).like(like_pattern),
                func.lower(Task.endDate).like(like_pattern),
                func.lower(Task.deadline).like(like_pattern),
                func.lower(Task.startDate).like(like_pattern)
            )
        )

    if specialSearch:
        if not typeOfSpecialSearch:
            return False
        if typeOfSpecialSearch == "maturita":
            specialConditions.append(Task.type == Type.Maturita)
            specialConditions.append(Task.guarantor == specialSearch)
        if typeOfSpecialSearch == "task":
            specialConditions.append(Task.type == Type.Task)
            specialConditions.append(Task.guarantor == specialSearch)
        if typeOfSpecialSearch == "guarantor":
            specialConditions.append(Task.guarantor == specialSearch)
        if typeOfSpecialSearch == "deadline":
            specialConditions.append(Task.deadline == specialSearch)
        if typeOfSpecialSearch == "endDate":
            specialConditions.append(Task.endDate == specialSearch)

    return Task.query.filter(and_(*conditions, *specialConditions)).offset(amountForPaging * pageNumber).limit(amountForPaging), Task.query.filter(and_(*conditions, *specialConditions)).count()

def team_paging(searchQuery, amountForPaging, pageNumber, specialSearch = None, typeOfSpecialSearch = None, ids = None, typeOfIds = None, typeOfTeam = None):
    words = [w.strip().lower() for w in searchQuery.split() if w.strip()]

    conditions = []
    specialConditions = []
    if typeOfTeam == "users":
        for word in words:
            like_pattern = f"%{word}%"
            conditions.append(
                or_(
                    func.lower(User.name).like(like_pattern),
                    func.lower(User.surname).like(like_pattern),
                    func.lower(User.email).like(like_pattern),
                    func.lower(User.abbreviation).like(like_pattern),
                )
            )

    else:
        for word in words:
            like_pattern = f"%{word}%"
            conditions.append(
                or_(
                    func.lower(Team.name).like(like_pattern)
                )
            )
    
    if specialSearch:
        if not typeOfSpecialSearch:
            return False

        if typeOfSpecialSearch == "status":
            specialConditions.append(Team.status == specialSearch)
        if typeOfSpecialSearch == "points":
            specialConditions.append(Team.points == specialSearch)

    if ids:
        if not isinstance(ids, list):
            ids = [ids]
        if typeOfIds == "task":
            specialConditions.append(Team.idTask.in_(ids))
        if typeOfIds == "elaboration":
            specialConditions.append(*ids)
    
    if typeOfTeam == "users":
        return Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).outerjoin(User, User_Team.idUser == User.id).filter(and_( *specialConditions, *conditions)).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).offset(amountForPaging * pageNumber).limit(amountForPaging), Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).outerjoin(User, User_Team.idUser == User.id).filter(and_( *specialConditions, *conditions)).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).count()
    
    return Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(and_(*conditions, *specialConditions)).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).offset(amountForPaging * pageNumber).limit(amountForPaging), Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(and_(*conditions, *specialConditions)).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).count()