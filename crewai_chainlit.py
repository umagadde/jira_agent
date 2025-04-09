from io import BytesIO
from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
import os
import pandas as pd  # Import pandas for data processing
import chainlit as cl
import os
from dataclasses import dataclass
from chainlit.element import Element
# Load environment variables
load_dotenv()

# Initialize LLM model
llm = LLM(
    model="sambanova/DeepSeek-R1-Distill-Llama-70B",
    temperature=0.7,
    max_tokens=2048
)

def speech_to_text(audio_path):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                return text  # Returning transcribed text for user editing
            except sr.UnknownValueError:
                return "Could not understand the audio"
            except sr.RequestError:
                return "Speech recognition service error"
    except :
        return ""

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
def clear_text():
    return ""

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

def process_query(user_query, audio_text=None):
    # checking the condition for which one has been provided
    if user_query:  # If audio is provided, convert to text
        dynamic_user = user_query
    else:
        dynamic_user = audio_text


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
        Just give the valid python code ..no extra commenst or print statements needed
        Encapsulate your output with //code start and //code end
        output should be in this format 
        Just giving you a context ..if user asks for backlog it means that sprintState should be Future for that issues no other column
        is required to find whether a issue is backlog or not
        '''
        //code start
        import pandas as pd
        df = pd.read_csv("generated_files/new_custom.csv")

        // your pandas generated code 
        // code saving it into generated_files/output.csv
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
            df = pd.read_csv("generated_files/output.csv") always use this 
            eg num_rows = len(df)
            eg column_sum = df["your_column_name"].sum() 
            if user is asking for individual or seperate result then calculate seperately 
            eg:rtb_count = (df["requested_by"] == "RTB").sum()
               tb_count = (df["requested_by"] == "CTB").sum()
            '''
            //code start
            import pandas as pd
            df = pd.read_csv("generated_files/output.csv")

            // your pandas generated code 
            // code for saving it into generated_files/output.txt with User Query followed by the output
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

        with open("generated_files/panda.py", "w") as f:
            f.write("\n")
            f.write(str(result2))
            f.write("\n")

        extract_code_section("generated_files/panda.py", "generated_files/output2.py")
        os.system("python generated_files/output2.py")
        os.system("python final.py")

            

        with open("generated_files/output.txt", "r") as f:
            output_content = f.read()

        # Getting the content to display in frontend 
        try:
            df = pd.read_csv("generated_files/output.csv")
            csv_download = "generated_files/output.csv"
        except FileNotFoundError:
            df = "output.csv not found."
            csv_download = None

        return output_content,df,'jira_hygiene_dashboard2.png',csv_download
    





@dataclass
class UIConfig:
    """Configuration for the Chainlit UI"""
    app_name: str = "JANVI - JIRA AI Assistant"
    theme_color: str = "#1E88E5"  
    support_audio: bool = True
    max_input_length: int = 500
    default_placeholder: str = "Enter your JIRA query here... 💡"

class JIRAAssistantUI:
    def __init__(self, config: UIConfig = UIConfig()):
        self.config = config

    @cl.on_chat_start
    async def start():
        """Initialize the chat interface"""
        await cl.Message(
            content=f"👋 Welcome to {UIConfig.app_name}! How can I help you with JIRA today?",
            author="Assistant"
        ).send()

    @cl.on_message
    async def process_message(message: str):
        """Main message processing handler"""
        # Validate input length
        if len(message.content) > UIConfig().max_input_length:
            await cl.Message(
                content=f"⚠️ Input too long. Maximum {UIConfig().max_input_length} characters allowed.",
                author="System"
            ).send()
            return

        # Show typing indicator
        async with cl.Step(name="Processing Query"):
            try:
                output_text, output_df,jira_hgn, output_file = process_query(message.content)

                if output_text:
                    await cl.Message(content=output_text).send()

                if output_df is not None :
                    # elements = [cl.Dataframe(data=df, display="inline", name="Dataframe")]
                    await cl.Message(
                        content="Here's the processed data:",
                        elements=[
                            cl.Dataframe(
                                data=output_df, 
                                display="inline",
                                name="JIRA Data",
                            
                            )
                        ]
                    ).send()

                if output_file and os.path.exists(output_file):
                    await cl.Message(
                        content="Your output file is ready for download.",
                        elements=[cl.File(name=os.path.basename(output_file), path=output_file)]
                    ).send()
                image = cl.Image(path=jira_hgn, name="Jira Hygene", display="inline")
                await cl.Message(
                    content="Jira Hygene Dashboard",
                    elements=[image],
                ).send()

            except Exception as e:
                await cl.Message(
                    content=f"🚨 Error processing your query: {str(e)}",
                    author="System"
                ).send()
                
    @cl.step(type="tool", name="Speech-to-Text")
    async def speech_to_text(audio_buffer: BytesIO) -> str:
        """Converts speech to text using Google SpeechRecognition API"""
        recognizer = sr.Recognizer()
        audio_buffer.seek(0)

        with sr.AudioFile(audio_buffer) as source:
            audio_data = recognizer.record(source)

            try:
                return recognizer.recognize_google(audio_data)
            except sr.UnknownValueError:
                return "Could not understand the audio"
            except sr.RequestError:
                return "Speech recognition service error"


    @cl.on_audio_chunk
    async def on_audio_chunk(chunk: cl.InputAudioChunk):
        """Handles incoming audio chunks and stores them in session"""
        if chunk.isStart:
            buffer = BytesIO()
            buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"  # Set filename
            cl.user_session.set("audio_buffer", buffer)
            cl.user_session.set("audio_mime_type", chunk.mimeType)

        cl.user_session.get("audio_buffer").write(chunk.data)


    @cl.on_audio_end
    async def on_audio_end(elements: list[Element]):
        """Processes recorded audio and converts it to text"""
        audio_buffer: BytesIO = cl.user_session.get("audio_buffer")
        audio_buffer.seek(0)
        audio_mime_type: str = cl.user_session.get("audio_mime_type")

        # Display the recorded audio
        input_audio_el = cl.Audio(mime=audio_mime_type, content=audio_buffer.read(), name=audio_buffer.name)
        await cl.Message(author="You", type="user_message", content="", elements=[input_audio_el, *elements]).send()

        # Convert speech to text
        transcription = await speech_to_text(audio_buffer)

        # Send transcribed text as a chat message
        msg = cl.Message(author="You", content=transcription, elements=elements)
        await msg.send()

    # Process the transcribed text as if it was a normal chat input
        await process_message(message=msg)

        # except Exception as e:
        #     await cl.Message(
        #         content=f"🔊 Audio processing error: {str(e)}",
        #         author="System"
        #     ).send()

    @cl.on_chat_end
    def end():
        """Clean up resources when chat ends"""
        # Add any necessary cleanup logic
        pass

def configure_chainlit_app():
    """Configure Chainlit application settings"""
    cl.App.config(
        name=UIConfig().app_name,
        theme=cl.Theme(
            primary_color=UIConfig().theme_color,
            font_family="Inter, sans-serif"
        ),
        enable_audio=True
    )

if __name__ == "__main__":
    configure_chainlit_app()
