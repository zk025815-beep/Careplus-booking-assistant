import json
from datetime import datetime
from openai import OpenAI

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, TIMEZONE, LOCAL_TZ
from rag_engine import search_clinic_knowledge_base
from google_services import get_available_slots, book_appointment_pipeline

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_clinic_knowledge_base",
            "description": "Search the clinic RAG knowledge base for business info, timings, services, pricing, location, and policies/FAQs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or search topic (e.g., 'services and prices', 'cancellation policy', 'clinic timings').",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_slots",
            "description": "Check Google Calendar for available 1-hour appointment time slots on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "The date to check in YYYY-MM-DD format (e.g., '2026-11-05').",
                    }
                },
                "required": ["date_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment_pipeline",
            "description": "Book and confirm an appointment ONLY AFTER collecting customer_name, email, service, date_str, and time_str, and AFTER the customer confirms an available slot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer.",
                    },
                    "email": {
                        "type": "string",
                        "description": "Email address of the customer for calendar invite and Gmail confirmation.",
                    },
                    "service": {
                        "type": "string",
                        "description": "Name of the clinic service being booked (e.g., 'Dental Checkup & Scaling', 'General Consultation').",
                    },
                    "date_str": {
                        "type": "string",
                        "description": "Appointment date in YYYY-MM-DD format.",
                    },
                    "time_str": {
                        "type": "string",
                        "description": "24-hour start time slot in HH:MM format (e.g., '10:00', '14:00').",
                    },
                },
                "required": [
                    "customer_name",
                    "email",
                    "service",
                    "date_str",
                    "time_str",
                ],
            },
        },
    },
]


def chat_with_assistant(user_message, history):
    today_str = datetime.now(LOCAL_TZ).strftime("%A, %Y-%m-%d")

    system_prompt = (
        f"You are the AI Appointment Booking Assistant for CarePlus Medical & Dental Clinic.\n"
        f"Current Date: {today_str} (Timezone: {TIMEZONE}).\n\n"
        f"Follow these rules strictly:\n"
        f"1. For any question about clinic services, prices, timings, location, or policies, ALWAYS call `search_clinic_knowledge_base` first.\n"
        f"2. When a user wants to book an appointment, you MUST collect 4 pieces of information: "
        f"(a) Customer's Full Name, (b) Email Address, (c) Service Type, and (d) Preferred Date/Time.\n"
        f"3. Once the user provides a preferred date, call `get_available_slots(date_str)` to check real-time availability on Google Calendar.\n"
        f"4. Present the available time slots clearly and ask the user to select/confirm their slot (and provide any missing info like name or email).\n"
        f"5. ONLY call `book_appointment_pipeline` once you have all 5 fields (customer_name, email, service, date_str in YYYY-MM-DD, time_str in HH:MM 24-hour format) and the user has agreed to the slot.\n"
        f"6. After booking, share the confirmation details and the Google Calendar event link with the customer."
    )

    messages = [{"role": "system", "content": system_prompt}]

    # Support both Gradio tuple and dictionary history formats
    for turn in history:
        if isinstance(turn, dict):
            content_val = turn.get("content", "")
            if isinstance(content_val, list):
                content_val = " ".join(
                    [b.get("text", "") if isinstance(b, dict) else str(b) for b in content_val]
                )
            messages.append({"role": turn["role"], "content": str(content_val)})
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            if turn[0]:
                messages.append({"role": "user", "content": str(turn[0])})
            if turn[1]:
                messages.append({"role": "assistant", "content": str(turn[1])})

    messages.append({"role": "user", "content": user_message})

    for _ in range(4):
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_msg = response.choices[0].message

        if not assistant_msg.tool_calls:
            return assistant_msg.content or "How else can I assist you today?"

        messages.append(assistant_msg)

        for tool_call in assistant_msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments)
            except Exception:
                fn_args = {}

            print(f"[Tool Call] Executing: {fn_name}({fn_args})")

            try:
                if fn_name == "search_clinic_knowledge_base":
                    tool_output = search_clinic_knowledge_base(fn_args.get("query", ""))
                elif fn_name == "get_available_slots":
                    slots = get_available_slots(fn_args.get("date_str", ""))
                    tool_output = json.dumps({"available_slots": slots})
                elif fn_name == "book_appointment_pipeline":
                    result = book_appointment_pipeline(
                        customer_name=fn_args.get("customer_name"),
                        email=fn_args.get("email"),
                        service=fn_args.get("service"),
                        date_str=fn_args.get("date_str"),
                        time_str=fn_args.get("time_str"),
                    )
                    tool_output = json.dumps(result)
                else:
                    tool_output = json.dumps({"error": f"Unknown tool: {fn_name}"})
            except Exception as e:
                tool_output = json.dumps({"error": str(e)})

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": fn_name,
                "content": str(tool_output),
            })

    return "I completed the actions, please let me know if you need anything else!"