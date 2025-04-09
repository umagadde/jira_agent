import pandas as pd
import random
from random import randint
from datetime import datetime, timedelta

#Define 6 sprints with 2 weeks duration
sprint_data={
    "Sprint 5": {"state":"Completed", "start_date": datetime(2024,2,26), "end_date": datetime(2024,3,11),"status":["Done"]},
    "Sprint 6": {"state":"Completed", "start_date": datetime(2024,3,12), "end_date": datetime(2024,3,25),"status":["Done"]},
    "Sprint 7": {"state":"Active", "start_date": datetime(2024,3,26), "end_date": datetime(2024,4,8),"status":["In Progress","Done","To Do"]},	
    "Sprint 8": {"state":"Future", "start_date": datetime(2024,4,9), "end_date": datetime(2024,4,22),"status":["To Do"]},	
    "Sprint 9": {"state":"Future", "start_date": datetime(2024,4,23), "end_date": datetime(2024,5,6),"status":["To Do"]},			

}

boards=["CDF","ESBNF"]
employement_type={
    "Alice": "FTC",
    "Bob": "FTC",
    "Rishika": "FTE",
    "Hari": "FTE",
    "Apoorva": "FTE",
    "David":"FTC",
    "Pavithra": "FTE",	
    "Alok": "FTE",
    "Peter": "FTC",

}

assignees={
    "CDF": ["Alice","Bob","Rishika","Hari","Apoorva"],
    "ESBNF": ["Apoorva","David","Pavithra","Alok","Peter"],
}

reporters={
    "CDF":["Tony","Naruto"],
    "ESBNF":["Zoro","Hinata"],	
}

priorities=["Low","Medium","High","Critical"]
issue_types=["Defect","Story","Task"]
CDF={"EPIC1":"RTB","EPIC2":"CTB","EPIC3":"RTB","EPIC4":"CTB"}
ESBNF={"EPIC5":"RTB","EPIC6":"CTB","EPIC7":"RTB"}		
Epic_issue_counts={"EPIC1":1,"EPIC2":1,"EPIC3":1,"EPIC4":1,"EPIC5":1,"EPIC6":1,"EPIC7":1}	

data=[]
for i in range(1,201):
    board=random.choice(boards)
    sprint_name=random.choice(list(sprint_data.keys()))
    sprint_details=sprint_data[sprint_name]
    sprint_start=sprint_details["start_date"]
    sprint_end=sprint_details["end_date"]
    sprint_state=sprint_details["state"]

    if(board=="CDF"):
        epic_id=random.choice(list(CDF.keys()))
        requested_by=CDF[epic_id]
    else:
        epic_id=random.choice(list(ESBNF.keys()))
        requested_by=ESBNF[epic_id]

    issue_type=random.choice(issue_types)
    priority=random.choice(priorities)

    assignee=random.choice(assignees[board])
    role=employement_type[assignee]
    reporter=random.choice(reporters[board])

    status=random.choice(sprint_details["status"])
    story_points=random.choice([1,2,3,5,8])

    issue_key=epic_id+"-"+str(Epic_issue_counts[epic_id])
    Epic_issue_counts[epic_id]+=1

    priority=random.choice(priorities)
    closed=None

    if(status in ["To Do","In Progress"]):
        closed=None
    else:
        if(sprint_state=="Completed"):
            closed=(sprint_end-timedelta(days=randint(1,13))).strftime("%Y-%m-%d")
        else:
            delta=datetime.today()-sprint_start
            closed=(sprint_start+timedelta(days=delta.days)).strftime("%Y-%m-%d")

    data.append({
        "key":issue_key,
        "board":board,
        "summary":f"TASK {i} for {board}",
        "description":f"Description for Task {i} in {board}",
        "acceptance_criteria":f"Acceptance criteria for issue type {issue_type} in {board} with issue key {issue_key}",
        "status": status,
        "assignee":assignee,
        "reporter":reporter,
        "priority":priority,
        "issue_type": issue_type,
        "created":(datetime.today()-timedelta(days=random.randint(5,30))).strftime("%Y-%m-%d"),
         "closed": closed,
         "labels":random.choice([["backend"],["frontend"],["bugfix"],["enhancement"],["UI"],[]]),
         "components":random.choice([["Auth Service"],["Payment Service"],["UI"],["API"],["Database"],[]]),
         "sprint":sprint_name,
         "sprint_state":sprint_state,
         "sprint_start_date":sprint_start.strftime("%Y-%m-%d"),
         "sprint_end_date":sprint_end.strftime("%Y-%m-%d"),
         "story_points":story_points,
         "epic_id":epic_id,
         "employee_type":role,
         "requested_by":requested_by,	
    })

for i in range(1,11):
    board="CDF"
    epic_id=random.choice(list(CDF.keys()))
    requested_by=CDF[epic_id]
    story_points=random.choice([1,2,3,5,8])
    issue_key=epic_id+"-"+str(Epic_issue_counts[epic_id])
    Epic_issue_counts[epic_id]+=1

    sprint_name=None
    sprint_state=None
    sprint_start=None
    sprint_end=None

    priority=random.choice(priorities)
    assignee=random.choice(assignees[board])
    role=employement_type[assignee]
    reporter=random.choice(reporters[board])

    issue_type=random.choice(issue_types)
    data.append({
        "key":issue_key,
        "board":board,
        "summary":f"Backlog {i} for {board}",
        "description":f"Description for unassigned backlog {i} in {board}",
        "acceptance_criteria":f"Acceptance criteria for issue type {issue_type} in {board} with issue key {issue_key}",
        "status": "To Do",
        "assignee":assignee,
        "reporter":reporter,
        "priority":priority,
        "issue_type": issue_type,
        "created":(datetime.today()-timedelta(days=random.randint(5,30))).strftime("%Y-%m-%d"),
         "closed": None,
         "labels":random.choice([["backend"],["frontend"],["bugfix"],["enhancement"],["UI"],[]]),
         "components":random.choice([["Auth Service"],["Payment Service"],["UI"],["API"],["Database"],[]]),
         "sprint":sprint_name,
         "sprint_state":sprint_state,
         "sprint_start_date":sprint_start,
         "sprint_end_date":sprint_end,
         "story_points":story_points,
         "epic_id":epic_id,
         "employee_type":role,
         "requested_by":requested_by,	
    })

for i in range(1,11):
    board="ESBNF"
    epic_id=random.choice(list(ESBNF.keys()))
    requested_by=ESBNF[epic_id]
    story_points=random.choice([1,2,3,5,8])
    issue_key=epic_id+"-"+str(Epic_issue_counts[epic_id])
    Epic_issue_counts[epic_id]+=1
    
    sprint_start=None
    sprint_end=None
    sprint_name=None
    sprint_state=None
    priority=random.choice(priorities)
    assignee=random.choice(assignees[board])
    role=employement_type[assignee]
    reporter=random.choice(reporters[board])
    issue_type=random.choice(issue_types)
    data.append({
        "key":issue_key,
        "board":board,
        "summary":f"Backlog {i} for {board}",
        "description":f"Description for unassigned backlog {i} in {board}",
        "acceptance_criteria":f"Acceptance criteria for issue type {issue_type} in {board} with issue key {issue_key}",
        "status": "To Do",
        "assignee":assignee,
        "reporter":reporter,
        "priority":priority,
        "issue_type": issue_type,
        "created":(datetime.today()-timedelta(days=random.randint(5,30))).strftime("%Y-%m-%d"),
         "closed": None,
         "labels":random.choice([["backend"],["frontend"],["bugfix"],["enhancement"],["UI"],[]]),
         "components":random.choice([["Auth Service"],["Payment Service"],["UI"],["API"],["Database"],[]]),
         "sprint":sprint_name,
         "sprint_state":sprint_state,
         "sprint_start_date":sprint_start,
         "sprint_end_date":sprint_end,
         "story_points":story_points,
         "epic_id":epic_id,
         "employee_type":role,
         "requested_by":requested_by,	
    })

df=pd.DataFrame(data)
df.to_csv("jira_data.csv",index=False)