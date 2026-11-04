import os
import base64
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    SCOPES,
    CREDENTIALS_FILE,
    TOKEN_FILE,
    SPREADSHEET_ID,
    TIMEZONE,
    LOCAL_TZ,
    BUSINESS_START_HOUR,
    BUSINESS_END_HOUR,
)


def init_google_services():import os
import json
import streamlit as st
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send"
]

def init_google_services():
    # 1. Auto-create token.json from Streamlit Secrets if running on Cloud
    if not os.path.exists("token.json"):
        token_data = os.getenv("GOOGLE_TOKEN_JSON")
        if not token_data:
            try:
                token_data = st.secrets.get("GOOGLE_TOKEN_JSON")
            except Exception:
                token_data = None
                
        if token_data:
            with open("token.json", "w") as f:
                f.write(token_data.strip())

    # 2. Load credentials from token.json
    if not os.path.exists("token.json"):
        raise FileNotFoundError(
            "token.json not found. Add GOOGLE_TOKEN_JSON to Streamlit Cloud Secrets."
        )

    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Refresh token if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())

    calendar_service = build("calendar", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)

    return calendar_service, sheets_service, gmail_service

    """Authenticates via OAuth 2.0 locally and returns Calendar, Sheets, and Gmail clients."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"'{CREDENTIALS_FILE}' not found in project root. "
                    "Place your downloaded OAuth client JSON file here."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Runs a local temporary web server to catch the OAuth callback automatically
            creds = flow.run_local_server(port=0, prompt="consent")

        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    calendar_service = build("calendar", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)
    return calendar_service, sheets_service, gmail_service


# Initialize services on module load
calendar_service, sheets_service, gmail_service = init_google_services()


def get_available_slots(date_str: str) -> list:
    """Checks Google Calendar for free 1-hour slots on a specific date (YYYY-MM-DD)."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return ["Error: Invalid date format. Please use YYYY-MM-DD."]

    day_start = LOCAL_TZ.localize(
        target_date.replace(hour=BUSINESS_START_HOUR, minute=0, second=0)
    )
    day_end = LOCAL_TZ.localize(
        target_date.replace(hour=BUSINESS_END_HOUR, minute=0, second=0)
    )

    body = {
        "timeMin": day_start.isoformat(),
        "timeMax": day_end.isoformat(),
        "timeZone": TIMEZONE,
        "items": [{"id": "primary"}],
    }
    events_result = calendar_service.freebusy().query(body=body).execute()
    busy_intervals = events_result["calendars"]["primary"]["busy"]

    available_slots = []
    current_slot = day_start

    while current_slot + timedelta(hours=1) <= day_end:
        slot_end = current_slot + timedelta(hours=1)
        is_conflict = False

        for busy in busy_intervals:
            busy_start = datetime.fromisoformat(
                busy["start"].replace("Z", "+00:00")
            ).astimezone(LOCAL_TZ)
            busy_end = datetime.fromisoformat(
                busy["end"].replace("Z", "+00:00")
            ).astimezone(LOCAL_TZ)

            if max(current_slot, busy_start) < min(slot_end, busy_end):
                is_conflict = True
                break

        if not is_conflict:
            available_slots.append(current_slot.strftime("%H:%M"))

        current_slot = slot_end

    return available_slots


def create_calendar_event(
    customer_name: str, email: str, service: str, date_str: str, time_str: str
) -> str:
    """Creates a real 1-hour appointment on Google Calendar."""
    start_dt = LOCAL_TZ.localize(
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    )
    end_dt = start_dt + timedelta(hours=1)

    event_body = {
        "summary": f"{service} - {customer_name}",
        "description": (
            f"Booked via AI Assistant.\nCustomer: {customer_name}\n"
            f"Email: {email}\nService: {service}"
        ),
        "start": {"dateTime": start_dt.isoformat(), "timeZone": TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": TIMEZONE},
        "attendees": [{"email": email}],
    }

    event = (
        calendar_service.events()
        .insert(calendarId="primary", body=event_body)
        .execute()
    )
    return event.get("htmlLink")


def save_to_google_sheets(
    customer_name: str, email: str, service: str, date_str: str, time_str: str
):
    """Appends a new booking record into the Google Sheet."""
    timestamp = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S")
    row_values = [[
        timestamp,
        customer_name,
        email,
        service,
        date_str,
        time_str,
        "Confirmed",
    ]]

    sheets_service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="A:G",
        valueInputOption="USER_ENTERED",
        body={"values": row_values},
    ).execute()


def send_confirmation_email(
    customer_name: str,
    email: str,
    service: str,
    date_str: str,
    time_str: str,
    cal_link: str,
):
    """Sends a real confirmation email to the customer using the Gmail API."""
    subject = f"Appointment Confirmed: {service} on {date_str}"
    body_text = (
        f"Hello {customer_name},\n\n"
        f"Your appointment has been successfully booked!\n\n"
        f"Details:\n"
        f"- Service: {service}\n"
        f"- Date: {date_str}\n"
        f"- Time: {time_str} ({TIMEZONE})\n"
        f"- Calendar Link: {cal_link}\n\n"
        f"Thank you for choosing CarePlus Medical & Dental Clinic!\n"
        f"Best regards,\nAI Booking Assistant"
    )

    message = MIMEText(body_text)
    message["to"] = email
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    gmail_service.users().messages().send(
        userId="me", body={"raw": raw_message}
    ).execute()


def book_appointment_pipeline(
    customer_name: str, email: str, service: str, date_str: str, time_str: str
) -> dict:
    """Verifies slot availability, creates Calendar event, logs to Sheet, and sends Gmail."""
    free_slots = get_available_slots(date_str)
    if time_str not in free_slots:
        return {
            "status": "error",
            "message": (
                f"Slot {time_str} on {date_str} is not available. "
                f"Free slots: {free_slots}"
            ),
        }

    cal_link = create_calendar_event(
        customer_name, email, service, date_str, time_str
    )
    save_to_google_sheets(customer_name, email, service, date_str, time_str)
    send_confirmation_email(
        customer_name, email, service, date_str, time_str, cal_link
    )

    return {
        "status": "success",
        "message": (
            f"Appointment confirmed for {customer_name} on {date_str} at {time_str}."
        ),
        "calendar_link": cal_link,
    }