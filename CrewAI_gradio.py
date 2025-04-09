import gradio as gr
from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
import os
import pandas as pd  # Import pandas for data processing

# Load environment variables
load_dotenv()

# Initialize LLM model
llm = LLM(
    model="sambanova/DeepSeek-R1-Distill-Llama-70B",
    temperature=0.7
)

# Function to extract code section from agent generated file
def extract_code_section(input_file, output_file):
    inside_code = False
    extracted_lines = []

    with open(input_file, "r", encoding="utf-8") as file:
        for line in file:
            if "//code start" in line:
                inside_code = True
                continue
            elif "//code end" in line:
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
    data_to_query: str
    specific_need: str

def process_query(dynamic_user):
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
        If there is nothing specific assign variable specific_need as "None" ''',
        agent=agent1,
        output_pydantic=extracted_info,
        expected_output="A response containing ",
    )

    crew0 = Crew(agents=[agent1], tasks=[task1])
    result0 = crew0.kickoff(inputs={"dynamic_user": dynamic_user})
    user_needs = result0["specific_need"]

    with open("checkpoint.txt", "a", encoding="utf-8") as f:
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

    with open("panda.py", "w") as f:
        f.write("\n")
        f.write(str(result1))
        f.write("\n")

    extract_code_section("panda.py", "output1.py")
    os.system("python output1.py")

    if user_needs == "None":
        with open('output.txt', 'w') as f:
            f.write(f"Nothing to write here as user did not ask anything specific.....\n")
        return "Nothing to write here as user did not ask anything specific....."
    else:
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

        task3 = Task(
            description=f'''Convert the user query User Query given in {prompt2} into a pandas code by understanding the csv file structure
            to query out specific need of the user and saving it into a text file named output.txt''',
            agent=agent2,
            expected_output="A pandas code to query out specific need of the user and saving it into a text file named output.txt",
        )

        crew2 = Crew(agents=[agent2], tasks=[task3])
        result2 = crew2.kickoff(inputs={"prompt2": prompt2})

        with open("panda.py", "w") as f:
            f.write("\n")
            f.write(str(result2))
            f.write("\n")

        extract_code_section("panda.py", "output2.py")
        os.system("python output2.py")

        with open("output.txt", "r") as f:
            output_content = f.read()

        try:
            df = pd.read_csv("output.csv")
            csv_output = gr.Dataframe(value=df, interactive=False)
            csv_download = gr.File("output.csv")
        except FileNotFoundError:
            csv_output = "output.csv not found."
            csv_download = None

        return output_content,csv_output,csv_download
js = """
function createGradioAnimation() {
    var container = document.createElement('div');
    container.id = 'gradio-animation';
    container.style.fontSize = '2em';
    container.style.fontWeight = 'bold';
    container.style.textAlign = 'center';
    container.style.marginBottom = '20px';

    var text = 'JANVI IS HERE!';
    var gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(container, gradioContainer.firstChild);

    function animateText() {
        container.innerHTML = ''; // Clear previous animation
        for (var i = 0; i < text.length; i++) {
            (function(i) {
                setTimeout(function() {
                    var letter = document.createElement('span');
                    letter.style.opacity = '0';
                    letter.style.transition = 'opacity 0.5s';
                    letter.innerText = text[i];
                    container.appendChild(letter);

                    setTimeout(function() {
                        letter.style.opacity = '1';
                    }, 50);
                }, i * 250);
            })(i);
        }
    }

    animateText();
    setInterval(animateText, text.length * 250 + 1000); // Repeat animation
    return 'Animation created';
}
"""

# Gradio Interface
iface = gr.Interface(
    fn=process_query,
    inputs=gr.Textbox(lines=2, placeholder="Enter your query here..."),
    outputs=[gr.Textbox(lines=10, label="Output"), gr.Dataframe(label="Formatted output.csv"),gr.File(label="Download output.csv")],
    title="JANVI - JIRA AI ASSISTANT",
    description="Enter your data query and get the processed result.",
    js=js
)

if __name__ == "__main__":
    iface.launch()