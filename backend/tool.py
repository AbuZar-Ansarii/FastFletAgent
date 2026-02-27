from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_community.tools import DuckDuckGoSearchRun
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import requests
import re
from langchain_community.document_loaders import YoutubeLoader

from langchain_experimental.tools import PythonREPLTool
from langchain_community.tools import ShellTool
from dotenv import load_dotenv
load_dotenv()

# Use the dedicated google-drive package paths
from langchain_googledrive.utilities.google_drive import GoogleDriveAPIWrapper
from langchain_googledrive.tools.google_drive.tool import GoogleDriveSearchTool


# 1. Configuration
api_path = r"E:\GEN AI PROJECT\graph-caht bot\LangGraph-Chat-Bot\client_secrets.json"
os.environ["GOOGLE_ACCOUNT_FILE"] = api_path


# 3. Initialize Tools properly
api_wrapper = GoogleDriveAPIWrapper() 
drive_tool = GoogleDriveSearchTool(api_wrapper=api_wrapper,template="gdrive-query", 
    num_results=10)



# ⚡ Configure your email credentials here
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")

@tool
def send_email(receiver: str, subject: str, content: str) -> str:
    """this tool can Send an email to the given receiver with subject and content."""
    try:
        # Validate receiver email
        validate_email(receiver)

        # Create email
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.attach(MIMEText(content, "plain"))

        # Send using SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver, msg.as_string())

        return f"✅ Email sent successfully to {receiver}"
    except EmailNotValidError:
        return "❌ Invalid receiver email address"
    except Exception as e:
        return f"❌ Failed to send email: {e}"


@tool
def text_to_pdf(text: str, output_path: str):
    """
    this tool can Converts a text string into a PDF file with basic text wrapping.
    """
    try:
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        
        # Set font and size
        c.setFont("Helvetica", 10)
        
        # Create a text object for better line handling
        text_obj = c.beginText(50, height - 50)
        text_obj.setLeading(14) # Space between lines
        
        # Split text by lines to preserve your paragraphs
        lines = text.split("\n")
        
        for line in lines:
            # Basic character-based wrapping (approx 90 chars for letter size)
            if len(line) > 90:
                # This breaks long lines into smaller chunks
                chunks = [line[i:i+90] for i in range(0, len(line), 90)]
                for chunk in chunks:
                    text_obj.textLine(chunk)
            else:
                text_obj.textLine(line)
            
            # Check for page overflow
            if text_obj.getY() < 50:
                c.drawText(text_obj)
                c.showPage()
                text_obj = c.beginText(50, height - 50)
                text_obj.setFont("Helvetica", 10)
                text_obj.setLeading(14)

        c.drawText(text_obj)
        c.save()
        return f"✅ PDF created successfully at: {os.path.abspath(output_path)}"
    
    except Exception as e:
        return f"❌ Error: {e}"


@tool
def drive_search(query: str) -> str:
    """this tool can search files in google drive."""
    results = drive_tool.run(query)
    return results


web_browser = TavilySearch(max_results=2)

@tool
def web_search(query: str) -> str:
    """this tool can search anything on web for current information."""
    results = web_browser.run(query)
    return results

@tool
def get_weather(city):
    '''this tool gives the current weather for a given city.'''
    # 1. convert city → lat/lon using Open-Meteo geocoding (free)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    geo_res = requests.get(geo_url).json()

    if "results" not in geo_res:
        return "City not found."

    lat = geo_res["results"][0]["latitude"]
    lon = geo_res["results"][0]["longitude"]

    # 2. get weather
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    weather_res = requests.get(weather_url).json()

    temp = weather_res["current_weather"]["temperature"]
    wind = weather_res["current_weather"]["windspeed"]

    return f"Weather in {city}:\nTemperature: {temp}°C\nWind Speed: {wind} km/h"


@tool
def get_transcript_langchain(url):
    "this tool retrieves the full text transcript of a YouTube video. Use this when the user asks questions about the content, summary, or specific details of a video by link."
    try:
        # This loader handles extraction and API calls internally
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
        docs = loader.load()
        
        # Combine page content from documents
        return " ".join([doc.page_content for doc in docs])
    except Exception as e:
        return f"Error: {str(e)}"


import os
import shutil
from pathlib import Path

@tool
def create_file(file_path: str, content: str) -> str:
    """
    Creates a new file at the specified path and writes the provided content into it.
    Use this when the user asks you to write code or save text to a file.
    Inputs:
    - file_path: The name or path of the file (e.g., 'prime_check.py' or 'scripts/app.py').
    - content: The actual text or code to write inside the file.
    """
    try:
        # Ensure the parent directory exists
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the content
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Success: File '{file_path}' created successfully."
    except Exception as e:
        return f"Error creating file: {str(e)}"

@tool
def move_file(source_path: str, destination_folder: str) -> str:
    """
    Moves an existing file into a new folder/directory.
    Use this when the user asks to organize, move, or place a file into a specific folder.
    Inputs:
    - source_path: The current path of the file (e.g., 'prime_check.py').
    - destination_folder: The folder where the file should go (e.g., 'my_scripts').
    """
    try:
        if not os.path.exists(source_path):
            return f"Error: The file '{source_path}' does not exist."
            
        # Ensure destination folder exists
        Path(destination_folder).mkdir(parents=True, exist_ok=True)
        
        # Move the file
        target_path = os.path.join(destination_folder, os.path.basename(source_path))
        shutil.move(source_path, target_path)
        
        return f"Success: File successfully moved to '{target_path}'."
    except Exception as e:
        return f"Error moving file: {str(e)}"

# 1. Initialize the built-in execution tools
python_repl = PythonREPLTool()
shell_tool = ShellTool()

tools = [get_weather, web_search, drive_search, send_email, text_to_pdf, get_transcript_langchain,create_file, move_file, python_repl, shell_tool]


# # Initialize the API wrapper
# api_wrapper = GoogleDriveAPIWrapper()

# # Create the search tool for the agent
# # This allows the agent to find files by name or content
# g_drive = GoogleDriveSearchTool(api_wrapper=api_wrapper)

