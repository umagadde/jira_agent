import csv
from datetime import datetime, timedelta
headers=[
    "name",
    "leave_type",
    "start_date",	
    "end_date",
    "total_days",
    "sprint"
]

sprint_data={
    "Sprint 5": {
        "start_date": datetime(2025, 2, 25),
        "end_date": datetime(2025, 3, 11),
        "status":["Done"]
    },
    "Sprint 6": {
        "start_date": datetime(2025, 3, 12),
        "end_date": datetime(2025, 3, 25),
        "status":["Done"]
    },
    "Sprint 7": {
        "start_date": datetime(2025, 3, 26),
        "end_date": datetime(2025, 4, 8),
        "status":["Done"]
    },
    "Sprint 8": {
        "start_date": datetime(2025, 4, 9),
        "end_date": datetime(2025, 4, 22),
        "status":["In Progress","Done","To Do"]	
    },
    "Sprint 9": {
        "start_date": datetime(2025, 4, 23),
        "end_date": datetime(2025, 5, 6),
        "status":["To Do"]	
    }
}
# Alice": "FTC",
#     "Bob": "FTC",
#     "Rishika": "FTE",
#     "Hari": "FTE",
#     "Apoorva": "FTE",
#     "David":"FTC",
#     "Pavithra": "FTE",	
#     "Alok": "FTE",
leave_data = [
    ["Alice","PTO",datetime(2025,2,26),datetime(2025,2,28),"3","Sprint 5"],
    ["Alice","optional holiday",datetime(2025,3,12),datetime(2025,3,12),1,"1","Sprint 6"],
    ["Alice","PTO",datetime(2025,3,26),datetime(2025,3,26),"1","Sprint 7"],
    ["Alice","sick leave",datetime(2025,4,11),datetime(2025,4,11),"1","Sprint 8"],
    ["Alice","PTO",datetime(2025,4,24),datetime(2025,4,25),"2","Sprint 9"],

    ["Bob","PTO",datetime(2025,3,5),datetime(2025,3,6),"2","Sprint 5"],
    ["Bob","sick leave",datetime(2025,4,13),datetime(2025,4,13),"1","Sprint 8"],
    ["Bob","PTO",datetime(2025,5,3),datetime(2025,5,3),"1","Sprint 9"],

    ["Hari","vacation",datetime(2025,3,2),datetime(2025,3,4),"3","Sprint 5"],
    ["Hari","PTO",datetime(2025,3,14),datetime(2025,3,14),"1","Sprint 6"],
    ["Hari","events",datetime(2025,3,25),datetime(2025,3,25),"1","Sprint 7"],

    ["Apoorva","PTO",datetime(2025,4,15),datetime(2025,4,16),"2","Sprint 8"],
    ["Apoorva","PTO",datetime(2025,5,1),datetime(2025,5,2),"2","Sprint 9"],	

    ["Pavithra","PTO",datetime(2025,4,24),datetime(2025,4,25),"2","Sprint 9"],

    ["Alok","PTO",datetime(2025,4,26),datetime(2025,4,29),"4","Sprint 9"],
    
]

with open("PTO.csv",mode="w") as file:
    writer=csv.writer(file)
    writer.writerow(headers)
    writer.writerows(leave_data)

print("PTO.csv file created successfully...happy coding")


