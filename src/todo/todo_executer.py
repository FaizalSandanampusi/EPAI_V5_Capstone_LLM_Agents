"""
Todo parsing and task execution module using Gemini-2.0-flash-exp.
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import yfinance as yf
from googleapiclient.discovery import build
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
import google.generativeai as genai

# Load configuration from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Gmail configuration from environment variables
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Import your LLM functions (adjust the import based on your project structure)
from src.llm.base_llm import generate_response, initialize_llm

def task_decoder(todo_file: str, agent: Optional[genai.GenerativeModel]) -> Optional[Dict[str, Any]]:
    """
    Parse a todo task using the Gemini LLM into predefined tasks.
    
    Args:
        todo_file (str): File that contains todo tasks in a text format.
        agent (LLM object): Gemini agent for this parsing task
        
    Returns:
        Optional[Dict[str, Any]]: Structured task data if successful,
                                  or an object with type "unknown" if not.
    """
    with open(todo_file, "r") as file:
        task_content = file.read()
    try:
        prompt = f"""
        Parse the following todo task and extract structured information:
        Task: {task_content}
        
        Very important note:
        
        For stock names, try to get the stock ticker symbol so that it is suitable to pass to the yfinance module.
        For example, Reliance Power is RPOWER.NS and Nvidia is NVDA.
        
        For date and time for calendar events read date in date in ISO 8601 format (e.g., "2025-03-01T09:00:00").
        If time is not mentioned take 9:00 AM as default. If duration is not mentioned take default as 15 mins.
        
        Return a JSON object with these fields based on the task type:
        1. For email reminders:
           {{"type": "normal_email", "subject":"subject","message": "message content", "reciever_email": "email address"}}
        2. For calendar invites:
           {{"type": "calendar_invite", "event": "event name", "date": "date/time", "duration": "duration in minutes", "email": "email address"}}
        3. For stock alerts:
           {{"type": "stock_alert", "symbol": "stock symbol", "time": "alert time", "email": "email address"}}
        
        If the task cannot be parsed into one of the above formats, return:
           {{"type": "unknown", "text": "readable tasks or line from file"}}
        
        Return only the JSON object.
        """
        response = generate_response(prompt, agent)
        if response:
            sanitized_response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(sanitized_response)
    except Exception as e:
        logger.error(f"Error in returning prompt response: {str(e)}")
        return None

def send_email(subject: str, body: str, recipient: str):
    """
    Send an email using Gmail.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, recipient, msg.as_string())
        
        logger.info(f"Email is sent to {recipient}")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

def create_calendar_event(event_name: str, event_date: str, recipient: str, duration: Optional[int] = 15):
    """
    Create a Google Calendar event using OAuth credentials.
    This function uses the InstalledAppFlow (with credentials.json/token.json) to authenticate.
    
    Args:
        event_name (str): Name/summary of the event.
        event_date (str): Start date/time in ISO 8601 format (e.g., "2025-03-01T09:00:00").
        recipient: A single email address (str) or a comma-separated string / list of emails.
        duration (int, optional): Duration of the event in minutes. Defaults to 15.
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('calendar', 'v3', credentials=creds)

        start_dt = datetime.fromisoformat(event_date)
        try:
            duration = int(duration)
        except Exception:
            duration = 15
        end_dt = start_dt + timedelta(minutes=duration)

        if isinstance(recipient, str):
            recipients = [r.strip() for r in recipient.split(",")]
        elif isinstance(recipient, list):
            recipients = recipient
        else:
            recipients = []
        attendees = [{"email": r} for r in recipients]

        event = {
            'summary': event_name,
            'description': 'Blocking time on calendar for project event',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'IST',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'IST',
            },
            'attendees': attendees,
            'reminders': {
                'useDefault': True,
            },
            'transparency': 'opaque'
        }

        created_event = service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        logger.info(f"Google Calendar invite is shared to: {', '.join(recipients)}. Event time: {start_dt.isoformat()}.  Event created: {created_event.get('htmlLink')}")
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")

def get_stock_price(symbol: str) -> Optional[float]:
    """
    Fetch the latest stock price using yfinance.
    """
    try:
        stock = yf.Ticker(symbol)
        price = round(stock.history(period="1d")["Close"].iloc[-1], 2)
        stock_info = stock.info
        currency = stock_info.get('currency', 'Currency information not available')
        logger.info(f"Stock {symbol} price is {price} {currency}")
        return price, currency
    except Exception as e:
        logger.error(f"Error fetching stock price for {symbol}: {str(e)}")
        return None

def handle_unknown_task(task: Dict[str, Any]):
    """
    Handle tasks that cannot be understood.
    """
    message = f"Cannot understand or execute task: {task.get('text', str(task))}"
    logger.warning(message)
    print(message)

def execute_task(task: Dict[str, Any]):
    """
    Execute a given todo task based on its type.
    """
    task_type = task.get("type", "unknown").lower()
    if task_type == "normal_email":
        if "message" in task and "reciever_email" in task:
            send_email(task["subject"], task["message"], task["reciever_email"])
        else:
            handle_unknown_task(task)
    elif task_type == "calendar_invite":
        if "event" in task and "date" in task and "email" in task:
            # Get duration if provided; default to 15 minutes if not.
            duration = task.get("duration", 15)
            create_calendar_event(task["event"], task["date"], task["email"], duration)
        else:
            handle_unknown_task(task)
    elif task_type == "stock_alert":
        if "symbol" in task and "time" in task and "email" in task:
            price, currency = get_stock_price(task["symbol"])
            if price is not None:
                message = f"The stock price for {task['symbol']} at {datetime.now()} is {price:.2f} {currency}"
                send_email("Stock Alert", message, task["email"])
            else:
                handle_unknown_task(task)
        else:
            handle_unknown_task(task)
    else:
        handle_unknown_task(task)

def process_tasks(todo_file: str, tasks_interpreter_agent: Optional[genai.GenerativeModel]):
    """
    Process all tasks from the given todo.txt file using the provided LLM agent.
    
    Args:
        todo_file (str): The path to the todo.txt file containing tasks.
        agent (Optional[genai.GenerativeModel]): The LLM agent instance used for parsing tasks.
    """
    tasks = task_decoder(todo_file, tasks_interpreter_agent)
    if tasks:
        if isinstance(tasks, dict):
            tasks = [tasks]
        for task in tasks:
            execute_task(task)
    else:
        logger.warning("No tasks were parsed from the todo file.")
