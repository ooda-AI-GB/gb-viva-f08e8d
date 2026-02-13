import os
import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status as http_status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
import uvicorn

# --- Configuration & Setup ---
os.makedirs("data", exist_ok=True)
DATABASE_URL = "sqlite:///./data/crm.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

templates = Jinja2Templates(directory="templates")
app = FastAPI(title="Sales CRM")

@app.get("/health")
def health():
    return {"status": "ok"}


# --- Database Models ---
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, index=True)
    status = Column(String, default="Lead")  # Lead, Contacted, Proposal, Closed
    competitive_intel = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    activities = relationship("Activity", back_populates="contact", cascade="all, delete-orphan")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    description = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    contact = relationship("Contact", back_populates="activities")

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Seeding Logic ---
def seed_data(db: Session):
    if db.query(Contact).first():
        return

    print("Seeding database...")
    initial_contacts = [
        {"name": "Alice Johnson", "email": "alice@techcorp.com", "company": "TechCorp", "status": "Lead", "intel": "Expanding to Europe next Q."},
        {"name": "Bob Smith", "email": "bob@startups.inc", "company": "Startups Inc", "status": "Contacted", "intel": "Considering competitor X due to pricing."},
        {"name": "Charlie Brown", "email": "charlie@enterprise.global", "company": "Enterprise Global", "status": "Proposal", "intel": "Budget approval pending board meeting."},
        {"name": "Diana Prince", "email": "diana@amazonia.net", "company": "Amazonia", "status": "Closed", "intel": "Long-term contract signed."},
        {"name": "Evan Wright", "email": "evan@logistics.co", "company": "Logistics Co", "status": "Lead", "intel": "Looking for fleet management solutions."},
        {"name": "Fiona Green", "email": "fiona@ecofriendly.org", "company": "EcoFriendly", "status": "Contacted", "intel": "Grant funding secured recently."},
        {"name": "George King", "email": "george@royal.ltd", "company": "Royal Ltd", "status": "Proposal", "intel": "Competitor Y offering 20% discount."},
        {"name": "Hannah White", "email": "hannah@medical.care", "company": "Medical Care", "status": "Closed", "intel": "Needs HIPAA compliance features."},
        {"name": "Ian Black", "email": "ian@construction.works", "company": "Construction Works", "status": "Lead", "intel": "New project starting in downtown."},
        {"name": "Jane Doe", "email": "jane@unknown.net", "company": "Unknown Net", "status": "Contacted", "intel": "Skeptical about cloud deployment."}
    ]

    for data in initial_contacts:
        contact = Contact(
            name=data["name"],
            email=data["email"],
            phone="555-0100",
            company=data["company"],
            status=data["status"],
            competitive_intel=data["intel"],
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=int(10 * (hash(data["name"]) % 10) / 10 + 1))
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

        # Add initial activity
        activity = Activity(
            contact_id=contact.id,
            description=f"Initial contact created via {data['status']} campaign.",
            timestamp=datetime.datetime.utcnow()
        )
        db.add(activity)
    
    db.commit()
    print("Database seeded.")

# --- Routes ---

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_data(db)
    db.close()

@app.get("/", response_class=HTMLResponse)
def kanban_board(request: Request, db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
    # Group by status
    grouped = {"Lead": [], "Contacted": [], "Proposal": [], "Closed": []}
    for c in contacts:
        if c.status in grouped:
            grouped[c.status].append(c)
    
    return templates.TemplateResponse("kanban.html", {
        "request": request, 
        "contacts_by_status": grouped,
        "active_page": "kanban"
    })

@app.get("/contacts", response_class=HTMLResponse)
def list_contacts(request: Request, db: Session = Depends(get_db)):
    contacts = db.query(Contact).order_by(Contact.created_at.desc()).all()
    return templates.TemplateResponse("contact_list.html", {
        "request": request, 
        "contacts": contacts,
        "active_page": "contacts"
    })

@app.get("/contacts/new", response_class=HTMLResponse)
def new_contact_form(request: Request):
    return templates.TemplateResponse("contact_edit.html", {
        "request": request, 
        "contact": None,
        "active_page": "contacts"
    })

@app.post("/contacts")
def create_contact(
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    status: str = Form("Lead"),
    competitive_intel: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    new_contact = Contact(
        name=name,
        email=email,
        phone=phone,
        company=company,
        status=status,
        competitive_intel=competitive_intel
    )
    db.add(new_contact)
    db.commit()
    return RedirectResponse(url="/contacts", status_code=http_status.HTTP_303_SEE_OTHER)

@app.get("/contacts/{contact_id}", response_class=HTMLResponse)
def edit_contact(contact_id: int, request: Request, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return templates.TemplateResponse("contact_edit.html", {
        "request": request, 
        "contact": contact,
        "active_page": "contacts"
    })

@app.post("/contacts/{contact_id}")
def update_contact(
    contact_id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    company: Optional[str] = Form(None),
    status: str = Form(...),
    competitive_intel: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.name = name
    contact.email = email
    contact.phone = phone
    contact.company = company
    contact.status = status
    contact.competitive_intel = competitive_intel
    
    db.commit()
    return RedirectResponse(url=f"/contacts/{contact_id}", status_code=http_status.HTTP_303_SEE_OTHER)

@app.post("/contacts/{contact_id}/activity")
def add_activity(
    contact_id: int,
    description: str = Form(...),
    db: Session = Depends(get_db)
):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    activity = Activity(contact_id=contact.id, description=description)
    db.add(activity)
    db.commit()
    
    return RedirectResponse(url=f"/contacts/{contact_id}", status_code=http_status.HTTP_303_SEE_OTHER)

@app.get("/intel", response_class=HTMLResponse)
def intel_view(request: Request, db: Session = Depends(get_db)):
    contacts = db.query(Contact).order_by(Contact.company).all()
    return templates.TemplateResponse("intel.html", {
        "request": request, 
        "contacts": contacts,
        "active_page": "intel"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
