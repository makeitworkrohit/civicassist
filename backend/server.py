from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from openai.llm.chat import LlmChat, UserMessage
from openai.llm.openai import OpenAISpeechToText
import io

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

JWT_SECRET = os.getenv('JWT_SECRET', 'civic-assist-secret-key-2026')
JWT_ALGORITHM = 'HS256'
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    password_hash: str
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    name: str
    state: str
    city: str
    pincode: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None

class Complaint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    original_input: str
    simplified_input: str
    category: str
    suggested_portal: Optional[dict] = None
    state: str
    city: str
    pincode: str
    confirmed: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SimplifyRequest(BaseModel):
    text: str

class PortalSuggestionRequest(BaseModel):
    category: str
    state: str
    city: str

class ComplaintSubmit(BaseModel):
    original_input: str
    simplified_input: str
    category: str
    confirmed: bool
    draft_subject: Optional[str] = None
    draft_description: Optional[str] = None

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    message: str

class DocumentSuggestRequest(BaseModel):
    category: str

class LocalHelpRequest(BaseModel):
    state: str
    city: str
    category: str

class Portal(BaseModel):
    name: str
    description: str
    url: str
    categories: List[str]
    states: List[str]
    guidance_steps: List[str]

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@api_router.get("/")
async def root():
    return {"message": "Civic Assist API"}

@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    password_hash = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=password_hash
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    token = create_token(user.id)
    return {
        "token": token,
        "user": UserResponse(**{k: v for k, v in user.model_dump().items() if k != 'password_hash'})
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'])
    user_response = UserResponse(**{k: v for k, v in user.items() if k != 'password_hash'})
    return {"token": token, "user": user_response}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(**{k: v for k, v in user.items() if k != 'password_hash'})

@api_router.put("/auth/profile")
async def update_profile(profile: UserProfile, user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": user['id']},
        {"$set": profile.model_dump()}
    )
    updated_user = await db.users.find_one({"id": user['id']}, {"_id": 0})
    return UserResponse(**{k: v for k, v in updated_user.items() if k != 'password_hash'})

@api_router.post("/complaint/transcribe")
async def transcribe_audio(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        audio_data = await file.read()
        audio_file = io.BytesIO(audio_data)
        audio_file.name = file.filename
        
        stt = OpenAISpeechToText(api_key=EMERGENT_LLM_KEY)
        response = await stt.transcribe(
            file=audio_file,
            model="whisper-1",
            response_format="json"
        )
        
        return {"text": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@api_router.post("/complaint/simplify")
async def simplify_complaint(request: SimplifyRequest, user: dict = Depends(get_current_user)):
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"simplify-{user['id']}-{uuid.uuid4()}",
            system_message="You are a complaint processing assistant. Simplify user complaints into clear, concise statements and classify them into categories like: Water Supply, Electricity, Road Maintenance, Waste Management, Public Transport, Healthcare, Education, Police, Revenue, Consumer Rights, or Other. Also generate a formal government-ready complaint with a subject line and detailed description. Return ONLY a valid JSON object with these keys: 'simplified' (brief summary), 'category' (complaint type), 'subject' (formal subject line for government portal), 'description' (formal detailed complaint description ready for submission). Do not use markdown formatting or code blocks."
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=f"Simplify this complaint, categorize it, and create a formal government-ready complaint draft with subject and description: {request.text}")
        response = await chat.send_message(user_message)
        
        import json
        import re
        
        # Clean the response - remove markdown code blocks if present
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
        cleaned_response = re.sub(r'^```\s*', '', cleaned_response)
        cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()
        
        try:
            result = json.loads(cleaned_response)
            # Ensure required keys exist
            if all(k in result for k in ['simplified', 'category', 'subject', 'description']):
                return {
                    "simplified": result['simplified'],
                    "category": result['category'],
                    "subject": result['subject'],
                    "description": result['description']
                }
            else:
                # Fallback if AI doesn't return all fields
                return {
                    "simplified": result.get('simplified', request.text),
                    "category": result.get('category', 'General Complaint'),
                    "subject": result.get('subject', f"Complaint regarding {result.get('category', 'General Issue')}"),
                    "description": result.get('description', request.text)
                }
        except:
            # If JSON parsing fails completely
            return {
                "simplified": request.text,
                "category": "General Complaint",
                "subject": "Complaint regarding General Issue",
                "description": request.text
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

@api_router.post("/complaint/submit")
async def submit_complaint(complaint_data: ComplaintSubmit, user: dict = Depends(get_current_user)):
    if not user.get('state') or not user.get('city'):
        raise HTTPException(status_code=400, detail="Please update your profile with location details")
    
    complaint = Complaint(
        user_id=user['id'],
        original_input=complaint_data.original_input,
        simplified_input=complaint_data.simplified_input,
        category=complaint_data.category,
        state=user['state'],
        city=user['city'],
        pincode=user.get('pincode', ''),
        confirmed=complaint_data.confirmed
    )
    
    doc = complaint.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.complaints.insert_one(doc)
    
    # Save complaint draft if provided
    if complaint_data.draft_subject and complaint_data.draft_description:
        draft_doc = {
            "id": str(uuid.uuid4()),
            "complaint_id": complaint.id,
            "user_id": user['id'],
            "subject": complaint_data.draft_subject,
            "description": complaint_data.draft_description,
            "category": complaint_data.category,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.complaint_drafts.insert_one(draft_doc)
    
    return {"id": complaint.id, "message": "Complaint submitted successfully"}

@api_router.get("/complaint/history")
async def get_complaint_history(user: dict = Depends(get_current_user)):
    complaints = await db.complaints.find({"user_id": user['id']}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    return complaints

@api_router.post("/documents/suggest")
async def suggest_documents(request: DocumentSuggestRequest, user: dict = Depends(get_current_user)):
    # Document suggestions based on category
    document_map = {
        "Electricity": [
            {"name": "Electricity Bill Copy", "required": True, "description": "Latest electricity bill showing account details"},
            {"name": "Identity Proof", "required": False, "description": "Aadhaar Card, PAN Card, or Voter ID"},
            {"name": "Photographs", "required": False, "description": "Photos of the issue (if applicable)"}
        ],
        "Water Supply": [
            {"name": "Water Bill Copy", "required": True, "description": "Latest water bill or connection proof"},
            {"name": "Address Proof", "required": True, "description": "Ration card, electricity bill, or rental agreement"},
            {"name": "Photographs", "required": False, "description": "Photos showing the water issue"}
        ],
        "Road Maintenance": [
            {"name": "Photographs", "required": True, "description": "Clear photos of potholes or road damage"},
            {"name": "Location Proof", "required": False, "description": "Google Maps screenshot or address"},
            {"name": "Identity Proof", "required": False, "description": "Any government ID"}
        ],
        "Consumer Rights": [
            {"name": "Purchase Invoice/Bill", "required": True, "description": "Original bill or receipt of purchase"},
            {"name": "Product Details", "required": True, "description": "Product photos, serial number, warranty card"},
            {"name": "Communication Records", "required": False, "description": "Emails, SMS, or call recordings with seller"}
        ],
        "Healthcare": [
            {"name": "Medical Records", "required": True, "description": "Prescriptions, test reports, treatment records"},
            {"name": "Hospital Bills", "required": True, "description": "Bills and payment receipts"},
            {"name": "Identity Proof", "required": True, "description": "Aadhaar Card or any government ID"}
        ],
        "Education": [
            {"name": "Admission Proof", "required": True, "description": "Admission receipt, student ID, or enrollment certificate"},
            {"name": "Fee Receipts", "required": False, "description": "Tuition fee payment receipts"},
            {"name": "Identity Proof", "required": True, "description": "Student ID or Aadhaar Card"}
        ]
    }
    
    # Default documents for general complaints
    default_docs = [
        {"name": "Identity Proof", "required": True, "description": "Aadhaar Card, PAN Card, Voter ID, or Passport"},
        {"name": "Address Proof", "required": False, "description": "Ration card, utility bill, or rental agreement"},
        {"name": "Supporting Evidence", "required": False, "description": "Photos, videos, or any relevant documents"}
    ]
    
    documents = document_map.get(request.category, default_docs)
    return {"category": request.category, "documents": documents}

@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    complaint_id: str = Form(...),
    user: dict = Depends(get_current_user)
):
    # Validate file type
    allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only PDF, JPG, and PNG files are allowed")
    
    # Validate file size (max 5MB)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 5MB")
    
    # In production, upload to S3 or cloud storage
    # For now, we'll store file info in database (mock file_url)
    file_id = str(uuid.uuid4())
    file_url = f"/uploads/{user['id']}/{complaint_id}/{file_id}_{file.filename}"
    
    doc = {
        "id": file_id,
        "user_id": user['id'],
        "complaint_id": complaint_id,
        "file_name": file.filename,
        "file_url": file_url,
        "file_type": file.content_type,
        "file_size": len(file_content),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.documents.insert_one(doc)
    
    return {
        "id": file_id,
        "file_name": file.filename,
        "file_url": file_url,
        "message": "Document uploaded successfully"
    }

@api_router.get("/documents/{complaint_id}")
async def get_documents(complaint_id: str, user: dict = Depends(get_current_user)):
    documents = await db.documents.find(
        {"complaint_id": complaint_id, "user_id": user['id']},
        {"_id": 0}
    ).to_list(100)
    return documents

@api_router.post("/locations/local-help")
async def get_local_help(request: LocalHelpRequest, user: dict = Depends(get_current_user)):
    # Local authority data (can be expanded with real data)
    local_authorities = {
        "Maharashtra": {
            "Mumbai": {
                "contacts": [
                    {
                        "office": "Mumbai Municipal Corporation - Complaint Cell",
                        "phone": "022-22694727",
                        "email": "complaints.mcgm@gmail.com",
                        "timings": "Mon-Sat, 10 AM - 6 PM"
                    },
                    {
                        "office": "Maharashtra Electricity Distribution Co. Ltd. (MSEDCL)",
                        "phone": "1912",
                        "email": "support@mahadiscom.in",
                        "timings": "24/7 Helpline"
                    }
                ],
                "offices": [
                    {
                        "name": "BMC Head Office",
                        "address": "Mahapalika Marg, Fort, Mumbai - 400001",
                        "department": "General Administration"
                    },
                    {
                        "name": "BEST Undertaking Office",
                        "address": "BEST Bhavan, Colaba Depot, Mumbai - 400005",
                        "department": "Electricity & Transport"
                    }
                ]
            }
        },
        "Karnataka": {
            "Bengaluru": {
                "contacts": [
                    {
                        "office": "BBMP Complaint Cell",
                        "phone": "080-22975000",
                        "email": "complaints@bbmp.gov.in",
                        "timings": "Mon-Sat, 9:30 AM - 5:30 PM"
                    },
                    {
                        "office": "BESCOM Helpline",
                        "phone": "1912",
                        "email": "bescom@karnataka.gov.in",
                        "timings": "24/7"
                    }
                ],
                "offices": [
                    {
                        "name": "BBMP Head Office",
                        "address": "N.R. Square, Bangalore - 560002",
                        "department": "Municipal Corporation"
                    }
                ]
            }
        },
        "Tamil Nadu": {
            "Chennai": {
                "contacts": [
                    {
                        "office": "Greater Chennai Corporation",
                        "phone": "044-25384520",
                        "email": "gcc@chennaicorporation.gov.in",
                        "timings": "Mon-Fri, 9 AM - 5 PM"
                    }
                ],
                "offices": [
                    {
                        "name": "Chennai Corporation Head Office",
                        "address": "Ripon Building, NSC Bose Road, Chennai - 600003",
                        "department": "Municipal Services"
                    }
                ]
            }
        },
        "Delhi": {
            "New Delhi": {
                "contacts": [
                    {
                        "office": "NDMC Complaint Cell",
                        "phone": "011-23321054",
                        "email": "complaints@ndmc.gov.in",
                        "timings": "Mon-Fri, 9 AM - 6 PM"
                    },
                    {
                        "office": "BSES Yamuna/Rajdhani Helpline",
                        "phone": "19123",
                        "email": "customercare@bsesdelhi.com",
                        "timings": "24/7"
                    }
                ],
                "offices": [
                    {
                        "name": "NDMC Office",
                        "address": "Palika Kendra, Sansad Marg, New Delhi - 110001",
                        "department": "Municipal Services"
                    }
                ]
            }
        }
    }
    
    # Get data for user's location
    state_data = local_authorities.get(request.state, {})
    city_data = state_data.get(request.city, {})
    
    # Default fallback
    if not city_data:
        city_data = {
            "contacts": [
                {
                    "office": "State Helpline",
                    "phone": "Use CPGRAMS portal for contact",
                    "email": "NA",
                    "timings": "Visit portal"
                }
            ],
            "offices": [
                {
                    "name": "District Collector Office",
                    "address": f"Contact local district office in {request.city}",
                    "department": "General Administration"
                }
            ]
        }
    
    return {
        "state": request.state,
        "city": request.city,
        "contacts": city_data.get("contacts", []),
        "offices": city_data.get("offices", []),
        "alternate_portals": []  # Can be populated later
    }

@api_router.post("/portal/suggest")
async def suggest_portal(request: PortalSuggestionRequest, user: dict = Depends(get_current_user)):
    # First, try to find state-specific portal matching the category
    portal = await db.portals.find_one(
        {
            "categories": request.category,
            "states": request.state
        },
        {"_id": 0}
    )
    
    # If no state-specific portal found, try All India portals for that category
    if not portal:
        portal = await db.portals.find_one(
            {
                "categories": request.category,
                "states": "All India"
            },
            {"_id": 0}
        )
    
    # If still no portal found, return CPGRAMS as default
    if not portal:
        portal = await db.portals.find_one(
            {
                "name": {"$regex": "CPGRAMS", "$options": "i"}
            },
            {"_id": 0}
        )
    
    # Final fallback
    if not portal:
        portal = {
            "name": "CPGRAMS - Centralized Public Grievance Redress System",
            "description": "National portal for lodging grievances to Government departments",
            "url": "https://pgportal.gov.in/",
            "guidance_steps": [
                "Visit the CPGRAMS portal",
                "Click on 'Lodge Public Grievance'",
                "Register or login to your account",
                "Fill in the grievance details",
                "Upload supporting documents if any",
                "Submit and note your registration number"
            ]
        }
    
    return portal

@api_router.post("/contact")
async def submit_contact(message: ContactMessage):
    doc = message.model_dump()
    doc['id'] = str(uuid.uuid4())
    doc['timestamp'] = datetime.now(timezone.utc).isoformat()
    await db.contact_messages.insert_one(doc)
    return {"message": "Thank you for contacting us!"}

@api_router.get("/locations/states")
async def get_states():
    states = [
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
        "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry"
    ]
    return {"states": states}

@api_router.get("/locations/cities/{state}")
async def get_cities(state: str):
    cities_map = {
        "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Tirupati", "Kakinada"],
        "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Pasighat", "Tawang", "Ziro"],
        "Assam": ["Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Tezpur", "Nagaon"],
        "Bihar": ["Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga", "Purnia"],
        "Chhattisgarh": ["Raipur", "Bhilai", "Bilaspur", "Korba", "Durg", "Rajnandgaon"],
        "Goa": ["Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar"],
        "Haryana": ["Chandigarh", "Faridabad", "Gurugram", "Panipat", "Ambala", "Karnal"],
        "Himachal Pradesh": ["Shimla", "Dharamshala", "Solan", "Mandi", "Kullu", "Hamirpur"],
        "Jharkhand": ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro", "Deoghar", "Hazaribagh"],
        "Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi", "Shivamogga"],
        "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Kannur"],
        "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain", "Sagar"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad", "Thane", "Solapur"],
        "Manipur": ["Imphal", "Thoubal", "Bishnupur", "Churachandpur", "Kakching"],
        "Meghalaya": ["Shillong", "Tura", "Jowai", "Nongstoin", "Williamnagar"],
        "Mizoram": ["Aizawl", "Lunglei", "Champhai", "Serchhip", "Kolasib"],
        "Nagaland": ["Kohima", "Dimapur", "Mokokchung", "Tuensang", "Wokha"],
        "Odisha": ["Bhubaneswar", "Cuttack", "Rourkela", "Brahmapur", "Sambalpur", "Puri"],
        "Punjab": ["Chandigarh", "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "Bikaner"],
        "Sikkim": ["Gangtok", "Namchi", "Gyalshing", "Mangan", "Rangpo"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli"],
        "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Khammam", "Karimnagar", "Ramagundam"],
        "Tripura": ["Agartala", "Udaipur", "Dharmanagar", "Kailashahar", "Ambassa"],
        "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Noida", "Ghaziabad", "Meerut"],
        "Uttarakhand": ["Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur", "Rishikesh"],
        "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri", "Bardhaman"],
        "Delhi": ["New Delhi", "Central Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"],
        "Jammu and Kashmir": ["Srinagar", "Jammu", "Anantnag", "Baramulla", "Udhampur", "Rajouri"],
        "Ladakh": ["Leh", "Kargil", "Nubra", "Zanskar"],
        "Puducherry": ["Puducherry", "Karaikal", "Mahe", "Yanam"]
    }
    return {"cities": cities_map.get(state, ["Other"])}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def seed_portals():
    existing = await db.portals.find_one({})
    if not existing:
        portals = [
            {
                "name": "Maharashtra Grievance Portal (Aaple Sarkar)",
                "description": "Official grievance portal for Maharashtra Government",
                "url": "https://grievances.maharashtra.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Maharashtra"],
                "guidance_steps": [
                    "Visit Maharashtra Grievance Portal",
                    "Click on 'Register Grievance'",
                    "Login with credentials or register new account",
                    "Select relevant department",
                    "Fill complaint form with details",
                    "Upload supporting documents if any",
                    "Submit and note grievance ID for tracking"
                ]
            },
            {
                "name": "Karnataka Sakala Services",
                "description": "Time-bound delivery of government services in Karnataka",
                "url": "https://sakala.karnataka.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Karnataka"],
                "guidance_steps": [
                    "Visit Sakala portal",
                    "Register or login to your account",
                    "Select service/complaint category",
                    "Fill application form",
                    "Upload required documents",
                    "Pay fees if applicable",
                    "Track application status online"
                ]
            },
            {
                "name": "Tamil Nadu Public Grievance Redressal System",
                "description": "Online grievance system for Tamil Nadu",
                "url": "https://www.tnpgrs.tn.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Tamil Nadu"],
                "guidance_steps": [
                    "Visit TN Grievance portal",
                    "Click 'Register Grievance'",
                    "Login or create account",
                    "Choose department and category",
                    "Provide complaint details",
                    "Submit with contact information",
                    "Track status using grievance number"
                ]
            },
            {
                "name": "Delhi Jansunwai Portal",
                "description": "Public grievance portal for Delhi Government",
                "url": "https://jansunwai.delhi.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Delhi"],
                "guidance_steps": [
                    "Visit Delhi Jansunwai portal",
                    "Register new complaint",
                    "Login with mobile/email",
                    "Select concerned department",
                    "Enter complaint details",
                    "Upload photos/documents",
                    "Submit and save complaint ID"
                ]
            },
            {
                "name": "Uttar Pradesh Jansunwai Portal",
                "description": "Grievance redressal system for UP",
                "url": "https://jansunwai.up.nic.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Uttar Pradesh"],
                "guidance_steps": [
                    "Visit UP Jansunwai portal",
                    "Click on 'शिकायत दर्ज करें' (Register Complaint)",
                    "Fill registration form",
                    "Select department",
                    "Provide complaint details",
                    "Submit and note grievance number"
                ]
            },
            {
                "name": "Gujarat CM Dashboard (Samadhan Portal)",
                "description": "Chief Minister's dashboard for public grievances",
                "url": "https://cmosamadhan.gujarat.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Gujarat"],
                "guidance_steps": [
                    "Visit CM Samadhan portal",
                    "Register complaint online",
                    "Fill complaint form",
                    "Select district and department",
                    "Upload documents if needed",
                    "Submit and track online"
                ]
            },
            {
                "name": "Rajasthan Sampark Portal",
                "description": "Integrated grievance portal for Rajasthan",
                "url": "https://sampark.rajasthan.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Rajasthan"],
                "guidance_steps": [
                    "Visit Sampark portal",
                    "Register new grievance",
                    "Login with credentials",
                    "Select complaint category",
                    "Fill details and submit",
                    "Track using mobile number"
                ]
            },
            {
                "name": "West Bengal Grievance Portal",
                "description": "Public grievance system for West Bengal",
                "url": "https://wb.gov.in/grievance-redressal.aspx",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["West Bengal"],
                "guidance_steps": [
                    "Visit WB Grievance portal",
                    "Click 'Submit Grievance'",
                    "Register or login",
                    "Choose department",
                    "Enter complaint details",
                    "Submit with verification"
                ]
            },
            {
                "name": "Andhra Pradesh Spandana Portal",
                "description": "Online grievance redressal for AP",
                "url": "https://spandana.ap.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Andhra Pradesh"],
                "guidance_steps": [
                    "Visit Spandana portal",
                    "Register grievance",
                    "Login with mobile OTP",
                    "Select category",
                    "Fill complaint form",
                    "Submit and track"
                ]
            },
            {
                "name": "Telangana CPGRAM State Portal",
                "description": "State grievance portal for Telangana",
                "url": "https://pgrs.telangana.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Telangana"],
                "guidance_steps": [
                    "Visit Telangana PGRS",
                    "Register complaint",
                    "Create account or login",
                    "Select department",
                    "Submit complaint details",
                    "Track status online"
                ]
            },
            {
                "name": "Kerala CM Grievance Portal",
                "description": "Chief Minister's grievance cell for Kerala",
                "url": "https://cm.lsgkerala.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Kerala"],
                "guidance_steps": [
                    "Visit CM Grievance portal",
                    "Submit new complaint",
                    "Fill personal details",
                    "Describe grievance",
                    "Upload documents",
                    "Submit and save reference number"
                ]
            },
            {
                "name": "Madhya Pradesh CM Helpline",
                "description": "Public grievance system for MP",
                "url": "https://cmhelpline.mp.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Madhya Pradesh"],
                "guidance_steps": [
                    "Visit CM Helpline portal",
                    "Register complaint online",
                    "Fill complaint form",
                    "Select district and category",
                    "Submit with details",
                    "Track using complaint ID"
                ]
            },
            {
                "name": "Bihar Jansunwai Portal",
                "description": "Public grievance portal for Bihar",
                "url": "https://serviceonline.bihar.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Bihar"],
                "guidance_steps": [
                    "Visit Bihar Jansunwai",
                    "Register grievance",
                    "Login to portal",
                    "Select service/complaint",
                    "Fill required details",
                    "Submit and track"
                ]
            },
            {
                "name": "Punjab Governance Reforms",
                "description": "Grievance system for Punjab",
                "url": "https://pgrs.punjab.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Punjab"],
                "guidance_steps": [
                    "Visit Punjab PGRS",
                    "Submit grievance",
                    "Register account",
                    "Select department",
                    "Provide complaint details",
                    "Submit and monitor"
                ]
            },
            {
                "name": "Haryana Antyodaya Saral Portal",
                "description": "Single window portal for Haryana services",
                "url": "https://saralharyana.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint"],
                "states": ["Haryana"],
                "guidance_steps": [
                    "Visit Saral Haryana portal",
                    "Register grievance",
                    "Create login credentials",
                    "Choose service",
                    "Fill application form",
                    "Track status online"
                ]
            },
            {
                "name": "CPGRAMS - Centralized Public Grievance Redress System",
                "description": "National portal for grievances (fallback for all states)",
                "url": "https://pgportal.gov.in/",
                "categories": ["Water Supply", "Electricity", "Road Maintenance", "Waste Management", "General Complaint", "Public Transport", "Healthcare", "Education", "Police", "Revenue"],
                "states": ["All India", "Arunachal Pradesh", "Assam", "Chhattisgarh", "Goa", "Himachal Pradesh", "Jharkhand", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Sikkim", "Tripura", "Uttarakhand", "Jammu and Kashmir", "Ladakh", "Puducherry"],
                "guidance_steps": [
                    "Visit CPGRAMS portal at pgportal.gov.in",
                    "Click 'Lodge Public Grievance'",
                    "Register with email/mobile or login",
                    "Select ministry/department/state",
                    "Fill complaint details clearly",
                    "Upload documents (if required)",
                    "Submit and save registration number for tracking"
                ]
            },
            {
                "name": "National Consumer Helpline",
                "description": "Consumer complaints and disputes resolution",
                "url": "https://consumerhelpline.gov.in/",
                "categories": ["Consumer Rights"],
                "states": ["All India"],
                "guidance_steps": [
                    "Visit consumerhelpline.gov.in",
                    "Register or login",
                    "Lodge your complaint",
                    "Provide bill/receipt details",
                    "Upload supporting documents",
                    "Track complaint status online"
                ]
            },
            {
                "name": "National Health Portal - Grievance",
                "description": "Healthcare related complaints",
                "url": "https://www.nhp.gov.in/",
                "categories": ["Healthcare"],
                "states": ["All India"],
                "guidance_steps": [
                    "Visit National Health Portal",
                    "Navigate to grievance section",
                    "Register complaint",
                    "Provide hospital/clinic details",
                    "Describe health service issue",
                    "Submit with supporting documents"
                ]
            },
            {
                "name": "Ministry of Education - Grievance Portal",
                "description": "Education related complaints and issues",
                "url": "https://pgportal.gov.in/",
                "categories": ["Education"],
                "states": ["All India"],
                "guidance_steps": [
                    "Visit CPGRAMS portal",
                    "Select Ministry of Education",
                    "Register complaint",
                    "Specify institution details",
                    "Describe educational grievance",
                    "Submit and track"
                ]
            },
            {
                "name": "Ministry of Road Transport - Grievance",
                "description": "Public transport and road safety complaints",
                "url": "https://pgportal.gov.in/",
                "categories": ["Public Transport"],
                "states": ["All India"],
                "guidance_steps": [
                    "Visit CPGRAMS portal",
                    "Select Ministry of Road Transport",
                    "Register complaint",
                    "Provide transport service details",
                    "Upload evidence if available",
                    "Submit and monitor status"
                ]
            }
        ]
        await db.portals.insert_many(portals)
        logger.info("Portal database seeded with state-specific portals")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
