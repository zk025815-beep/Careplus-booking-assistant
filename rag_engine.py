import chromadb
from chromadb.utils import embedding_functions

# Persistent local ChromaDB storage inside ./chroma_db
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="clinic_knowledge_base",
    embedding_function=embedding_fn,
)

CLINIC_DOCS = [
    "Clinic Name & Location: CarePlus Medical & Dental Clinic, located at Main Boulevard, Gulgasht Colony, Multan. Contact phone: +92-300-1234567.",
    "Operating Hours & Timings: We are open Monday to Saturday from 9:00 AM to 5:00 PM PKT (Asia/Karachi). All appointments are 1-hour slots starting on the hour (09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00, 16:00). We are closed on Sundays.",
    "Services & Pricing: 1) General Consultation (Rs. 2,000) - Complete physical checkup and diagnosis. 2) Dental Checkup & Scaling (Rs. 3,500) - Teeth cleaning, plaque removal, and dental exam. 3) Skin & Dermatology Consultation (Rs. 2,500) - Acne, allergy, and skin treatment. 4) Physiotherapy Session (Rs. 3,000) - Joint pain and rehab therapy.",
    "Booking & Cancellation Policy: Customers must provide their full name, email address, service type, and preferred date and time to book an appointment. Cancellations or rescheduling must be done at least 24 hours in advance. No-shows may be charged a 50% booking fee.",
    "FAQ - Insurance & Payment: We accept cash, bank transfer, SadaPay, JazzCash, and major credit/debit cards. We provide stamped medical invoices for corporate insurance reimbursement.",
    "FAQ - Preparation & Arrival: Please arrive 10 minutes prior to your scheduled slot and bring any previous medical reports or prescriptions.",
]

# Populate only if collection is empty
if collection.count() == 0:
    collection.add(
        documents=CLINIC_DOCS,
        ids=[f"doc_{i}" for i in range(len(CLINIC_DOCS))],
    )


def search_clinic_knowledge_base(query: str) -> str:
    """Queries the RAG vector store for clinic policies, timings, services, and FAQs."""
    results = collection.query(query_texts=[query], n_results=3)
    retrieved_chunks = results["documents"][0]
    return "\n\n".join(retrieved_chunks)