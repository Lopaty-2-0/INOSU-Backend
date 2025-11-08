from sqlalchemy import or_, func, and_
from src.models.User import User
from src.models.Specialization import Specialization
from src.models.Class import Class
from src.models.Task import Task

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

    if specialSearch:
        #I dont think we will use any other than the role
        if not typeOfSpecialSearch:
            return False
        
        if typeOfSpecialSearch == "createdAt":
            specialConditions.append(User.createdAt == specialSearch)
        if typeOfSpecialSearch == "role":
            specialConditions.append(User.role == specialSearch)
        if typeOfSpecialSearch == "updatedAt":
            specialConditions.append(User.updatedAt == specialSearch)

    return User.query.filter(and_(*conditions, *specialConditions)).offset(amountForPaging * pageNumber).limit(amountForPaging)

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

    return Specialization.query.filter(and_(*conditions)).offset(amountForPaging * pageNumber).limit(amountForPaging)

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

    return Class.query.filter(and_(*conditions)).offset(amountForPaging * pageNumber).limit(amountForPaging)

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
        #I dont think we will use any other than the role
        if not typeOfSpecialSearch:
            return False
        
        if typeOfSpecialSearch == "guarantor":
            specialConditions.append(Task.guarantor == specialSearch)
        if typeOfSpecialSearch == "deadline":
            specialConditions.append(Task.deadline == specialSearch)
        if typeOfSpecialSearch == "endDate":
            specialConditions.append(Task.endDate == specialSearch)

    return Task.query.filter(and_(*conditions)).offset(amountForPaging * pageNumber).limit(amountForPaging)
