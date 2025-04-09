from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
import os
import pandas as pd  # Import pandas for data processing
import chainlit as cl
from typing import Optional





# Load environment variables
load_dotenv()

# Initialize LLM model
llm = LLM(
    model="sambanova/DeepSeek-R1-Distill-Llama-70B",
    temperature=0.1,
    max_tokens=2048
)


# Function to extract code section from agent generated file
def extract_code_section(input_file, output_file):
    inside_code = False
    extracted_lines = []

    with open(input_file, "r", encoding="utf-8") as file:
        for line in file:
            if "#code start" in line:
                inside_code = True
                continue
            elif "#code end" in line:
                inside_code = False
                break
            if inside_code:
                extracted_lines.append(line)

    with open(output_file, "w", encoding="utf-8") as file:
        file.writelines(extracted_lines)

    os.remove(input_file)


# DataFrame structure
df_structure = """
The dataset has the following columns:
- "key": issue key
- "board": board id to which the issue has been assigned to
- "summary": summary of issues
- "description": description of issue
- "status": ["To Do", "In Progress", "Done"]
- "assignee": assigned person's name
- "reporter": reporter's name
- "acceptance_criteria": acceptance criteria
- "priority": ["High", "Medium", "Low", "Critical"]
- "issue_type": ["Story", "Bug", "Task","Defect"]
- "created": date of creation for the issue (YYYY-MM-DD)
- "closed": closed date (MM-DD-YYYY) , None if issue is not closed
- "labels": List of label names
- "components": List of component names
- "sprint": sprint name
- "sprint_state": ["Completed", "Active", "Future"]
- "sprint_start_date": sprint start date (MM-DD-YYYY)
- "sprint_end_date": sprint end date (MM-DD-YYYY)
- "story_points": story points (numeric)
- "epic_id": epic id 
- "requested_by": RTB or CTB
- "employee_type": employee type of assignee ( FTE or FTC )
"""

class extracted_info(BaseModel):
    data_to_query: str
    specific_need: str

async def process_query(user_query: str):
    # checking the condition for which one has been provided
    dynamic_user = user_query

    # Agent 1: Query info extraction
    agent1 = Agent(
        role="User Query analyzer",
        goal="performing the given task to maximum reliability",
        backstory="You are a data expert specializing in analyzing and extracting information from user query",
        llm=llm,
        verbose=True,
    )

    task1 = Task(
        description=f'''From the user query {dynamic_user} extract 2 things : 1. What data has to be queried(data_to_query)2. Is there anything specific the user is asking for(specific_need)
        For example if the user query is "Sum of all story points assigned to David" then data_to_query will be "All issues assigned to David" and specific_need will be "sum of all story points of David
        If there is nothing specific assign variable specific_need as "None" 
        eg if query is total number story points assigned to RTB , CTB seperately in Sprint 8 then
        data_to_query: All issues in Sprint 8
        specific_need: Stroy points assigned to RTB , CTB seperately
        eg2 if query is total number of story points assigned to Rishika and Alok in sprint 8
        data_to_query: All issues assigned to Rishika and Alok in sprint 8
        specific_need: Story points assigned to Rishika and Alok seperately in sprint 8
        eg3 if query is total number of backlogs in CDF board in Sprint 8
        data_to_query: All backlogs in CDF board in Sprint 8
        specific_need: Number of backlogs in CDF board in Sprint 8
        eg: if query is total number of story points assigned to David 
        data_to_query: All issues assigned to David
        specific_need: Sum of all story points assigned to David
        ''',
        agent=agent1,
        output_pydantic=extracted_info,
        expected_output="A response containing ",
    )

    crew0 = Crew(agents=[agent1], tasks=[task1])
    result0 = crew0.kickoff(inputs={"dynamic_user": dynamic_user})
    user_needs = result0["specific_need"]

    with open("generated_files/checkpoint.txt", "a", encoding="utf-8") as f:
        f.write("Date and Time :" + str(datetime.now()) + "\n")
        f.write("users original query :" + dynamic_user + "\n")
        f.write("data to query  :" + result0["data_to_query"] + "\n")
        f.write("specific need  :" + result0["specific_need"] + "\n")
        f.write("------------------------------------------------------------------" + "\n")

    # Agent 2: Pandas query generation
    prompt1 = f"""
        You are an expert in Pandas and data analysis. Convert the following natural language request into a valid Pandas DataFrame query.

        DataFrame Structure:
        {df_structure}

        Request: "{result0['data_to_query']}"

        Ensure the output is a valid Pandas query.
        Just give the valid python code ..no extra comments or print statements needed
        Just giving you a context ..if user asks for backlog it means that sprintState should be Future for that issues no other column is required to find whether a issue is backlog or not
        Encapsulate your output with #code start and #code end
        output should be in this format 
        #code start
        import pandas as pd
        df = pd.read_csv("generated_files/new_custom.csv")

        // your pandas generated code 
        // code saving it into generated_files/output.csv
        #code end 
        """

    agent2 = Agent(
        role="Pandas Query Agent",
        goal="Generate and execute Pandas queries from user requests.",
        backstory="You are a data expert specializing in analyzing and extracting information from Pandas DataFrames.",
        llm=llm,
        verbose=True,
    )

    task2 = Task(
        description=f"Convert user queries given in {prompt1} into Pandas queries by understanding the dataframe structure given in {prompt1} and return the perfectly working queries",
        agent=agent2,
        expected_output="A pandas query that filters the DataFrame based on the given prompt.",
    )

    crew1 = Crew(agents=[agent2], tasks=[task2])
    result1 = crew1.kickoff(inputs={"prompt1": prompt1})

    with open("generated_files/panda.py", "w") as f:
        f.write("\n")
        f.write(str(result1))
        f.write("\n")

    extract_code_section("generated_files/panda.py", "generated_files/output1.py")
    os.system("python generated_files/output1.py")

    if user_needs == "None":
        with open('generated_files/output.txt', 'w') as f:
            f.write(f"Nothing to write here as user did not ask anything specific.....\n")
        return "Nothing to write here as user did not ask anything specific....."
    else:
        prompt2 = f"""
            You are given a CSV file with structure {df_structure}
            Analyze the data and provide a concise pandas code that should run on output.csv file to query the result and also
            to save it in a output.txt file .

            User Query: "{user_needs}"

            output should be in this format there should be code start and code end like given below 
            If they ask you to count anything then dont try to filter the dataframe . use df functions 
            Dont create any new dataframe after df ..assume every needed data is already filtered out in df and use it to calculate
            Dont use any other dataframe name other than df
            eg: df = pd.read_csv("generated_files/output.csv")
            df = pd.read_csv("generated_files/output.csv") always use this 
            eg num_rows = len(df)
            eg column_sum = df["your_column_name"].sum() 
            if user is asking for individual or seperate result then calculate seperately 
            eg:rtb_count = (df["requested_by"] == "RTB").sum()
               tb_count = (df["requested_by"] == "CTB").sum()
            eg code ...
            #code start
            import pandas as pd
            df = pd.read_csv("generated_files/output.csv")

            // your pandas generated code 
            // code for saving it into generated_files/output.txt with User Query followed by the output
            #code end 
            """

        task3 = Task(
            description=f'''Convert the user query User Query given in {prompt2} into a pandas code by understanding the csv file structure
            to query out specific need of the user and saving it into a text file named output.txt''',
            agent=agent2,
            expected_output="A pandas code to query out specific need of the user and saving it into a text file named output.txt",
        )

        crew2 = Crew(agents=[agent2], tasks=[task3])
        result2 = crew2.kickoff(inputs={"prompt2": prompt2})

        with open("generated_files/panda.py", "w") as f:
            f.write("\n")
            f.write(str(result2))
            f.write("\n")

        extract_code_section("generated_files/panda.py", "generated_files/output2.py")
        os.system("python generated_files/output2.py")
        os.system("python final.py")

        return None
    

# This is where the frontend chainlit part starts............
os.environ["CHAINLIT_AUTH_SECRET"]="my_secret_key"


# Predefined user credentials (username: password)
PRESET_CREDENTIALS = {
    "Manoj.Kalyanasundaram@wellsfargo.com": "manoj",
    "Uma.Bhargave@wellsfargo.com": "uma",
    "manager": "manager"
}

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    # Check if credentials match
    if username=="Manoj.Kalyanasundaram@wellsfargo.com" and PRESET_CREDENTIALS[username] == password:
        return cl.User(identifier=username, metadata={"role": "developer","name":"Manoj"})
    elif username=="Uma.Bhargave@wellsfargo.com" and PRESET_CREDENTIALS[username] == password:
        return cl.User(identifier=username, metadata={"role": "developer","name":"Uma"})
    elif username=="manager" and PRESET_CREDENTIALS[username] == password:
        return cl.User(identifier=username, metadata={"role": "manager","name":"Manager"})
    else:
        return None
    

# as we are using welcome messages at the start ..these starters wont matter
@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label="Total number of story points assigned to David in Sprint 8",
            message="Total number of story points assigned to David in Sprint 8",
            icon="/public/icon.svg",
            ),

        cl.Starter(
            label="Total number of backlogs assigned Sprint 8",
            message="Total number of backlogs assigned Sprint 8",
            icon="/public/icon.svg",
            ),
        cl.Starter(
            label="Total number of backlogs assigned CDF board",
            message="Total number of backlogs assigned CDF board",
            icon="/public/icon.svg",
            ),
        ]

@cl.on_chat_start
async def start():
    """Initialize the chat interface"""
    # Get the current user
    user = cl.user_session.get("user")
    
    # Access the user's metadata
    if user:
        name = user.metadata.get("name")
        role = user.metadata.get("role")

    if(role=="developer"):
        welcome_message = f"👋 Welcome {name} (Role: {role}) to JIRA AI Assistant! Test me so that we wont get any future errors"
    else:
        welcome_message = f"👋 Welcome {name} (Role: {role}) to JIRA AI Assistant! This is what your interns Built..."
    
    await cl.Message(
        content=welcome_message,
        author="Assistant"
    ).send() 


@cl.step(type="tool")
async def process1(message):
    await process_query(message)

    with open("generated_files/output.txt", "r") as f:
        output_content = f.read()
    try:
        df = pd.read_csv("generated_files/output.csv")
        csv_download = "generated_files/output.csv"
    except FileNotFoundError:
        df = "output.csv not found."
        csv_download = None

    await cl.Message(
        content=f"We found that...{output_content}",
    ).send()

    await cl.Message(
            content="Here's the processed data:",
            elements=[
                cl.Dataframe(
                    data=df, 
                    display="inline",
                    name="JIRA Data",
                
                )
            ]
            ).send()
    image = cl.Image(path='jira_hygiene_dashboard2.png', name="Jira Hygene", display="inline")
    await cl.Message(
        content="Jira Hygene Dashboard",
        elements=[image],
    ).send()

    return "Process1 completed successfully"



@cl.on_message
async def process_message(message: str):
    """Main message processing handler"""
    # Validate input length
    if len(message.content) > 500:
        await cl.Message(
            content=f"⚠️ Input too long. Maximum 500 characters allowed.",
            author="System"
        ).send()
    tool_res = await process1(message.content)
    print(tool_res)
    

