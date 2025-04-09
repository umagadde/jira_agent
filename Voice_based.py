import gradio as gr
from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
import os
import pandas as pd  # Import pandas for data processing
import speech_recognition as sr
import matplotlib.pyplot as plt


# Load environment variables
load_dotenv()

# Initialize LLM model
llm = LLM(
    model="sambanova/DeepSeek-R1-Distill-Llama-70B",
    temperature=0.7,
    max_tokens=2048
)

def speech_to_text(audio_path):
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
        specific_need: Stroy points assigned to RTB , CTB seperately''',
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
            csv_output = gr.Dataframe(value=df, interactive=False)
            csv_download = gr.File("generated_files/output.csv")
        except FileNotFoundError:
            csv_output = "output.csv not found."
            csv_download = None

        return output_content,csv_output,'jira_hygiene_dashboard2.png',csv_download
    


# Frontend part starts ............
js="""
function createPremiumIntroAnimation() {
    // Create animation container
    const animationContainer = document.createElement('div');
    animationContainer.id = 'janvi-premium-intro';
    animationContainer.style.cssText = `
        position: relative;
        width: 100%;
        height: 120px;
        margin: 2rem 0;
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
    `;
    
    // Create text element
    const textElement = document.createElement('div');
    textElement.style.cssText = `
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #0052cc, #36b37e, #ff5630);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        position: relative;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        opacity: 0;
        transform: translateY(30px);
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.2));
    `;
    textElement.innerText = 'JANVI AI ASSISTANT';
    
    // Create particle container
    const particleContainer = document.createElement('div');
    particleContainer.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    `;
    
    // Create decorative elements
    const leftOrnament = document.createElement('div');
    const rightOrnament = document.createElement('div');
    [leftOrnament, rightOrnament].forEach((el, i) => {
        el.style.cssText = `
            position: absolute;
            top: 50%;
            ${i === 0 ? 'left' : 'right'}: 10%;
            width: 60px;
            height: 4px;
            background: linear-gradient(${i === 0 ? 'to right' : 'to left'}, #0052cc, #36b37e);
            transform: translateY(-50%) scaleX(0);
            transform-origin: ${i === 0 ? 'left' : 'right'};
            border-radius: 2px;
            opacity: 0;
        `;
    });
    
    // Assemble the components
    animationContainer.appendChild(textElement);
    animationContainer.appendChild(particleContainer);
    animationContainer.appendChild(leftOrnament);
    animationContainer.appendChild(rightOrnament);
    
    // Insert into DOM
    const gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(animationContainer, gradioContainer.firstChild);
    
    // Animation timeline
    const tl = {
        duration: 2000,
        start: Date.now(),
        animate: function() {
            const elapsed = Date.now() - this.start;
            const progress = Math.min(elapsed / this.duration, 1);
            
            // Text animation
            textElement.style.opacity = progress;
            textElement.style.transform = `translateY(${30 * (1 - progress)}px)`;
            
            // Ornament animation
            if (progress > 0.3) {
                const ornamentProgress = (progress - 0.3) / 0.7;
                leftOrnament.style.opacity = ornamentProgress;
                rightOrnament.style.opacity = ornamentProgress;
                leftOrnament.style.transform = `translateY(-50%) scaleX(${ornamentProgress})`;
                rightOrnament.style.transform = `translateY(-50%) scaleX(${ornamentProgress})`;
            }
            
            // Continue animation until complete
            if (progress < 1) {
                requestAnimationFrame(() => this.animate());
            } else {
                this.createParticles(particleContainer);
            }
        },
        createParticles: function(container) {
            // Create 30 particles
            for (let i = 0; i < 30; i++) {
                setTimeout(() => {
                    const particle = document.createElement('div');
                    const size = Math.random() * 8 + 4;
                    const color = `hsl(${Math.random() * 60 + 180}, 80%, 60%)`;
                    
                    particle.style.cssText = `
                        position: absolute;
                        width: ${size}px;
                        height: ${size}px;
                        background: ${color};
                        border-radius: 50%;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        opacity: 0;
                        filter: blur(${size/3}px);
                    `;
                    
                    container.appendChild(particle);
                    
                    // Animate particle
                    const angle = Math.random() * Math.PI * 2;
                    const distance = Math.random() * 100 + 50;
                    const duration = Math.random() * 2000 + 1000;
                    
                    particle.animate([
                        { 
                            opacity: 1,
                            transform: `translate(-50%, -50%) scale(1)`
                        },
                        {
                            opacity: 0,
                            transform: `translate(
                                ${-50 + Math.cos(angle) * distance}%, 
                                ${-50 + Math.sin(angle) * distance}%
                            ) scale(0)`
                        }
                    ], {
                        duration: duration,
                        easing: 'cubic-bezier(0.4, 0, 0.2, 1)'
                    });
                    
                    // Remove particle after animation
                    setTimeout(() => {
                        particle.remove();
                    }, duration);
                }, i * 100);
            }
            
            // Repeat particle effect every 3 seconds
            setTimeout(() => this.createParticles(container), 3000);
        }
    };
    
    // Start animation
    setTimeout(() => tl.animate(), 500);
    
    return 'Premium animation initialized';
}
"""

css="""
/* === Full-Page Premium Gradient Theme === */
.gradio-container {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #82b1ff 100%);
    font-family: 'Poppins', 'Roboto', sans-serif;
    width: 100vw;
    min-height: 100vh;
    padding: 0;
    margin: 0;
    animation: gradientFlow 15s ease infinite;
    background-size: 200% 200%;
    position: relative;
    overflow-x: hidden;
}

@keyframes gradientFlow {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* === Main Content Card === */
.gradio-container > .container {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 20px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
    padding: 3rem;
    max-width: 1000px;
    margin: 3rem auto;
    border: 1px solid rgba(255, 255, 255, 0.3);
    animation: fadeInUp 0.8s cubic-bezier(0.22, 1, 0.36, 1);
    transform-origin: top center;
}

/* === Header Styling === */
h1 {
    text-align: center;
    font-weight: 800;
    font-size: 3rem;
    margin: 0 0 1.5rem 0;
    background: linear-gradient(135deg, #1e88e5 0%, #0d47a1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    position: relative;
    padding-bottom: 1.5rem;
}

h1::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 150px;
    height: 4px;
    background: linear-gradient(90deg, #1e88e5, #0d47a1);
    border-radius: 2px;
    box-shadow: 0 2px 8px rgba(30, 136, 229, 0.3);
}

/* === Input Fields === */
.gr-textbox, .gr-input {
    border-radius: 14px !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    padding: 1.25rem !important;
    transition: all 0.3s ease !important;
    background: rgba(255, 255, 255, 0.8) !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
}

.gr-textbox:focus, .gr-input:focus {
    border-color: #1e88e5 !important;
    box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.2) !important;
    transform: translateY(-2px);
}

/* === Enhanced Buttons === */
.gr-button {
    background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%) !important;
    color: white !important;
    border: none !important;
    padding: 1.25rem 2.5rem !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(30, 136, 229, 0.4) !important;
    position: relative;
    overflow: hidden;
    margin: 2rem auto !important;
    display: block;
    width: fit-content;
    min-width: 220px;
}

.gr-button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 6px 20px rgba(30, 136, 229, 0.6) !important;
    background: linear-gradient(135deg, #2196f3 0%, #1e88e5 100%) !important;
}

.gr-button::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -60%;
    width: 200%;
    height: 200%;
    background: linear-gradient(
        to right,
        rgba(255, 255, 255, 0) 0%,
        rgba(255, 255, 255, 0.3) 50%,
        rgba(255, 255, 255, 0) 100%
    );
    transform: rotate(30deg);
    transition: all 0.6s ease;
}

.gr-button:hover::after {
    left: 100%;
}

/* === Audio Input Styling === */
.gr-audio {
    border-radius: 16px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    transition: all 0.3s ease !important;
}

.gr-audio:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15) !important;
}

/* === Output Sections === */
.gr-dataframe, .gr-file {
    border-radius: 16px !important;
    border: 1px solid rgba(0, 0, 0, 0.1) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
    transition: all 0.3s ease !important;
}

.gr-dataframe:hover, .gr-file:hover {
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1) !important;
    transform: translateY(-2px);
}

/* === Animations === */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* === Floating Particles === */
.gradio-container::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
        radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.15) 0%, transparent 2%),
        radial-gradient(circle at 80% 70%, rgba(30, 136, 229, 0.1) 0%, transparent 2%);
    background-size: 300px 300px;
    pointer-events: none;
    z-index: 0;
}

/* === Responsive Design === */
@media (max-width: 768px) {
    .gradio-container > .container {
        padding: 2rem;
        margin: 2rem 1rem;
        border-radius: 16px;
    }
    
    h1 {
        font-size: 2.25rem;
    }
    
    .gr-button {
        padding: 1rem 2rem !important;
        min-width: 180px;
    }
}

/* === Custom Scrollbar === */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(#1e88e5, #1565c0);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(#2196f3, #1e88e5);
}"""

def validate_and_process(text, transcribed):
    if not text and not transcribed:
        gr.Warning("⚠️ Please enter either a text query or provide an audio input.⚠️")
        return None, None, None  # Prevents processing if no input is given
    return process_query(text, transcribed)  # Call your actual processing function

with gr.Blocks(js=js, css=css) as iface:
    #gr.Markdown("# JANVI - JIRA AI ASSISTANT")
    gr.Markdown("Enter your query using text or voice. You can edit transcribed text before submission.")

    with gr.Row():
        text_input = gr.Textbox(lines=2, placeholder="Enter your query here...", label="Query Input")
        audio_input = gr.Audio(type="filepath", label="Speak your query")
    
    transcribed_text = gr.Textbox(lines=2, label="Transcribed Text (Edit if needed)")

    audio_input.change(speech_to_text, inputs=audio_input, outputs=transcribed_text)
    
    process_btn = gr.Button("Submit Query")

    output_text = gr.Textbox(lines=10, label="Output")
    output_df = gr.Dataframe(label="Issues retrieved")
    # Create a row for the image and file download
    with gr.Row():
        output_image = gr.Image(label="JIRA hygiene Report") 
        output_file = gr.File(label="Download output.csv")

    process_btn.click(validate_and_process, inputs=[text_input, transcribed_text], outputs=[output_text, output_df, output_image, output_file])

if __name__ == "__main__":
    iface.launch()

# handling the None cases for specific user query........























# css = """
# /* General container styling */
# .gradio-container {
#     background: linear-gradient(135deg, #e3f2fd, #bbdefb);
#     font-family: 'Roboto', sans-serif;
#     width: 100vw;
#     max-width: 100%;
#     min-height: 100vh;
#     padding: 40px;
#     border-radius: 15px;
#     box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
#     max-width: 900px;
#     margin: 50px auto;
#     animation: fadeIn 1s ease-in-out;
# }
# button:hover {
#     background: linear-gradient(135deg, #1e88e5, #1565c0);
#     transform: translateY(-2px);
# }

# /* Fade-in animation */
# @keyframes fadeIn {
#     from {
#         opacity: 0;
#         transform: translateY(-20px);
#     }
#     to {
#         opacity: 1;
#         transform: translateY(0);
#     }
# }

# /* Fade-in-out animation for the welcome text */
# @keyframes fadeInOut {
#     0%, 100% {
#         opacity: 0;
#     }
#     50% {
#         opacity: 1;
#     }
# }
# """

   
# js = """
# function createGradioAnimation() {
#     var container = document.createElement('div');
#     container.id = 'gradio-animation';
#     container.style.fontSize = '2em';
#     container.style.fontWeight = 'bold';
#     container.style.textAlign = 'center';
#     container.style.marginBottom = '20px';

#     var text = 'JANVI IS HERE!';
#     var gradioContainer = document.querySelector('.gradio-container');
#     gradioContainer.insertBefore(container, gradioContainer.firstChild);

#     function animateText() {
#         container.innerHTML = ''; // Clear previous animation
#         for (var i = 0; i < text.length; i++) {
#             (function(i) {
#                 setTimeout(function() {
#                     var letter = document.createElement('span');
#                     letter.style.opacity = '0';
#                     letter.style.transition = 'opacity 0.5s';
#                     letter.innerText = text[i];
#                     container.appendChild(letter);

#                     setTimeout(function() {
#                         letter.style.opacity = '1';
#                     }, 50);
#                 }, i * 250);
#             })(i);
#         }
#     }

#     animateText();
#     setInterval(animateText, text.length * 250 + 1000); // Repeat animation
#     return 'Animation created';
# }
# """