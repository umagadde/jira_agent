from crewai import Agent, Task, Crew,LLM
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
import os

# Load the environment variables from the .env file ( sambanova API key is stored in the .env file)
load_dotenv()

# Initiliazing the LLM model for the agent which will act as the brain of the agent
llm = LLM(
    model="sambanova/DeepSeek-R1-Distill-Llama-70B",
    temperature=0.7
)


# user queries for testing 

user_query1 = "Filter the DataFrame to show only the tasks with priority 'High'"
user_query2="All the issues that are assigned to David and have a status of 'In Progress'"
user_query3="All the issues under E-Commerce project those priority is 'Critical'"
dynamic_user=input("enter the query for us to process : ")

# Function to extract the code section from the agent generated file 
def extract_code_section(input_file, output_file):
    """
    Extracts the lines between '//code start' and '//code end' from a given Python file.
    
    :param input_file: Path to the input Python file.
    :param output_file: Path to save the extracted code.
    """
    inside_code = False
    extracted_lines = []

    with open(input_file, "r", encoding="utf-8") as file:
        for line in file:
            if "//code start" in line:
                inside_code = True
                continue  # Skip the marker line
            elif "//code end" in line:
                inside_code = False
                break  # Stop reading after //code end
            
            if inside_code:
                extracted_lines.append(line)

    with open(output_file, "w", encoding="utf-8") as file:
        file.writelines(extracted_lines)

    print(f"Extracted code saved to: {output_file}")
    os.remove(input_file)
    print(f"Deleted original file: {input_file}")


# The dataframe structure 
df_structure = """
The dataset has the following columns:
- "id": unique identifier
- "key": issue key
- "project": project name
- "summary": summary of project
- "description": description of task
- "status": ["Backlog", "To Do", "In Progress", "Review", "Done"]
- "assignee": assigned person's name
- "reporter": reporter's name
- "priority": ["High", "Medium", "Low", "Critical"]
- "issuetype": ["Story", "Bug", "Task", "Epic"]
- "created": date of creation (YYYY-MM-DD)
- "updated": last update date (YYYY-MM-DD)
- "resolution": ["Fixed", "Won't Fix", "Duplicate", None]
- "labels": labels (list)
- "components": components involved
- "sprint": sprint name
- "sprintId": sprint ID
- "sprintState": ["To Do", "In Progress", "Review", "Done"]
- "sprintStartDate": sprint start date (YYYY-MM-DD)
- "sprintEndDate": sprint end date (YYYY-MM-DD)
- "storyPoints": story points (numeric)
- "epicLink": linked epic
- "rank": rank
"""

class extracted_info(BaseModel):
    data_to_query:str
    specific_need:str


# Define agent for query info extraction 
agent1= Agent(
    role="User Query analyzer",
    goal="performing the given task to maximum reliability",
    backstory="You are a data expert specializing in analyzing and extracting information from user query",
    llm=llm,
    verbose=True,
)

# defining task for the agent1
task1=Task(
    description='''From the user query {dynamic_user} extract 2 things : 1. What data has to be queried(data_to_query)2. Is there anything specific the user is asking for(specific_need)
    For example if the user query is "Sum of all story points assigned to David" then data_to_query will be "All issues assigned to David" and specific_need will be "sum of all story points of David
    If there is nothing specific assign variable specific_need as "None" ''',
    agent=agent1,
    output_pydantic=extracted_info,
    expected_output="A response containing ",
)

crew0= Crew(agents=[agent1], tasks=[task1])
result0 = crew0.kickoff(inputs={"dynamic_user":dynamic_user})
user_needs=result0["specific_need"]

with open("checkpoint.txt", "a", encoding="utf-8") as f:
    f.write("Date and Time :"+str(datetime.now())+"\n")
    f.write("users original query :"+dynamic_user+"\n")
    f.write("data to query  :"+result0["data_to_query"]+"\n")
    f.write("specific need  :"+result0["specific_need"]+"\n")
    f.write("------------------------------------------------------------------"+"\n")


# Prompt containing user query , dataframe structure and expected output to gude our agent
prompt1= f"""
    You are an expert in Pandas and data analysis. Convert the following natural language request into a valid Pandas DataFrame query.

    DataFrame Structure:
    {df_structure}

    Request: "{result0['data_to_query']}"

    Ensure the output is a valid Pandas query.
    Just give the valid python code ..no extra commenst or print statements needed
    Encapsulate your output with //code start and //code end
    output should be in this format 
    '''
    //code start
    import pandas as pd
    df = pd.read_csv("new_custom.csv")

    // your pandas generated code 
    // code saving it into output.csv
    '''

    """

# Define the CrewAI Agent for pandas query generation 
agent2 = Agent(
    role="Pandas Query Agent",
    goal="Generate and execute Pandas queries from user requests.",
    backstory="You are a data expert specializing in analyzing and extracting information from Pandas DataFrames.",
    llm=llm,
    verbose=True,
)

# Define the Task
task2 = Task(
    description="Convert user queries given in {prompt1} into Pandas queries by understanding the dataframe structure given in {prompt1} and return the perfectly working queries",
    agent=agent2,
    expected_output="A pandas query that filters the DataFrame based on the given prompt.",
)

# Create the Crew with one agent and one task 
crew1 = Crew(agents=[agent2], tasks=[task2])

# Running  the agent
result1 = crew1.kickoff(inputs={"prompt1": prompt1})

# writing initial code to a file for later processing 
with open("panda.py", "w") as f:
    f.write("\n")
    f.write(str(result1))
    f.write("\n")


# Post processing of generated data to extract the useful code
extract_code_section("panda.py", "output1.py")

#Running the code using os library manually 
os.system("python output1.py")


if (user_needs=="None"):
    with open('output.txt', 'w') as f:
        f.write(f"Nothing to write here as user did not ask anything specific.....\n")
else:
    # Now we to address the specific users query so that we have output in the textual format ( easy for leadership )
    # creating a promt template 
    prompt2 = f"""
        You are given a CSV file with structure {df_structure}
        Analyze the data and provide a concise pandas code that should run on output.csv file to query the result and also
        to save it in a output.txt file .
        
        User Query: "{user_needs}"
        
        output should be in this format there should be code start and code end like given below 
        '''
        //code start
        import pandas as pd
        df = pd.read_csv("output.csv")

        // your pandas generated code 
        // code for saving it into output.txt with User Query followed by the output
        //code end 
        '''

        """
    # defining a task for the agent above 
    task3 = Task(
        description='''Convert the user query User Query given in {prompt2} into a pandas code by understanding the csv file structure
        to query out specific need of the user and saving it into a text file named output.txt''',
        agent=agent2,
        expected_output="A pandas code to query out specific need of the user and saving it into a text file named output.txt",
    )

    # initializing the second crew for the agent and task
    crew2 = Crew(agents=[agent2], tasks=[task3])

    # Run second agent to analyze `output.csv` and user's query to generate the final output
    result2 = crew2.kickoff(inputs={"prompt2": prompt2})

    with open("panda.py", "w") as f:
        f.write("\n")
        f.write(str(result2))
        f.write("\n")

    # Post processing of generated data to extract the useful code
    extract_code_section("panda.py", "output2.py")

    #Running the code using os library manually 
    os.system("python output2.py")