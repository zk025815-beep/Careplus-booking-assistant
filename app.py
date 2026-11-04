import gradio as gr
from agent import chat_with_assistant

demo = gr.ChatInterface(
    fn=chat_with_assistant,
    title="🏥 CarePlus Clinic — AI Appointment Booking Assistant",
    description=(
        "Ask about our **services, prices, clinic timings, or policies** (powered by RAG), "
        "or **book a real appointment** synced with Google Calendar, Google Sheets, and Gmail!"
    ),
    examples=[
        "What services do you offer and what are your charges?",
        "What are your clinic timings and cancellation policy?",
        "I want to book a Dental Checkup for tomorrow.",
    ],
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=10000)