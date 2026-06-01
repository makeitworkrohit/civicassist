from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import asyncio
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import hashlib
import secrets
from openai import AsyncOpenAI
import io
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

JWT_SECRET = os.environ['JWT_SECRET']  # MUST be set — no insecure fallback
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
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserProfile(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(default='', max_length=10)

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
    text: str = Field(..., min_length=10, max_length=5000)

class PortalSuggestionRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    pincode: Optional[str] = None

class ComplaintSubmit(BaseModel):
    original_input: str
    simplified_input: str
    category: str
    confirmed: bool
    draft_subject: Optional[str] = None
    draft_description: Optional[str] = None

class ContactMessage(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=10, max_length=2000)

class DocumentSuggestRequest(BaseModel):
    category: str

class LocalHelpRequest(BaseModel):
    state: str
    city: str
    category: str
    pincode: Optional[str] = None

class Portal(BaseModel):
    name: str
    description: str
    url: str
    categories: List[str]
    states: List[str]
    guidance_steps: List[str]

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    iterations = 100000
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt}${key.hex()}"

def verify_password(password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("pbkdf2_sha256$"):
        try:
            parts = hashed_password.split('$')
            if len(parts) != 4:
                return False
            _, iterations_str, salt, original_hash = parts
            iterations = int(iterations_str)
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                iterations
            )
            return secrets.compare_digest(key.hex(), original_hash)
        except Exception:
            return False
    elif hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    return False

async def hash_password_async(password: str) -> str:
    """Run CPU-bound hashing in a thread pool so the event loop stays free."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, hash_password, password)

async def verify_password_async(password: str, hashed_password: str) -> bool:
    """Run CPU-bound verification in a thread pool so the event loop stays free."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, verify_password, password, hashed_password)

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
@limiter.limit("3/minute")
async def register(request: Request, user_data: UserRegister):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Offload CPU-heavy hashing to thread pool — keeps event loop responsive
    password_hash = await hash_password_async(user_data.password)
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
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Offload CPU-heavy verification to thread pool — keeps event loop responsive
    if not await verify_password_async(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Auto-migrate password hash to high-performance PBKDF2-SHA256 if user logged in using old bcrypt hash
    if user['password_hash'].startswith("$2b$") or user['password_hash'].startswith("$2a$"):
        try:
            new_hash = await hash_password_async(credentials.password)
            await db.users.update_one(
                {"id": user['id']},
                {"$set": {"password_hash": new_hash}}
            )
            user['password_hash'] = new_hash
        except Exception:
            pass
    
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
@limiter.limit("5/minute")
async def transcribe_audio(request: Request, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    try:
        audio_data = await file.read()
        audio_file = io.BytesIO(audio_data)
        audio_file.name = file.filename
        
        openai_client = AsyncOpenAI(api_key=EMERGENT_LLM_KEY)
        response = await openai_client.audio.transcriptions.create(
            file=(file.filename, audio_file, file.content_type),
            model="whisper-1",
            response_format="json"
        )
        
        return {"text": response.text}
    except Exception as e:
        logger.error(f"Transcription failed for user {user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(status_code=500, detail="Transcription failed. Please try again.")

@api_router.post("/complaint/simplify")
@limiter.limit("10/minute")
async def simplify_complaint(request: Request, simplify_request: SimplifyRequest, user: dict = Depends(get_current_user)):
    try:
        openai_client = AsyncOpenAI(api_key=EMERGENT_LLM_KEY)
        completion = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a complaint processing assistant. Simplify user complaints into clear, concise statements and classify them into categories like: Water Supply, Electricity, Road Maintenance, Waste Management, Public Transport, Healthcare, Education, Police, Revenue, Consumer Rights, or Other. Also generate a formal government-ready complaint with a subject line and detailed description. Return ONLY a valid JSON object with these keys: 'simplified' (brief summary), 'category' (complaint type), 'subject' (formal subject line for government portal), 'description' (formal detailed complaint description ready for submission). Do not use markdown formatting or code blocks."
                },
                {
                    "role": "user",
                    "content": f"Simplify this complaint, categorize it, and create a formal government-ready complaint draft with subject and description: {simplify_request.text}"
                }
            ]
        )
        response = completion.choices[0].message.content
        
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
                    "simplified": result.get('simplified', simplify_request.text),
                    "category": result.get('category', 'General Complaint'),
                    "subject": result.get('subject', f"Complaint regarding {result.get('category', 'General Issue')}"),
                    "description": result.get('description', simplify_request.text)
                }
        except:
            # If JSON parsing fails completely
            return {
                "simplified": simplify_request.text,
                "category": "General Complaint",
                "subject": "Complaint regarding General Issue",
                "description": simplify_request.text
            }
    except Exception as e:
        logger.error(f"AI processing failed for user {user.get('id', 'unknown')}: {str(e)}")
        raise HTTPException(status_code=500, detail="AI processing failed. Please try again.")

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
    prompt = f"""
    You are an expert civic assistant for India with deep knowledge of municipal corporations, state government departments, and local civic bodies.
    The user needs to know the correct local government offline offices and official helpline numbers for their civic issue.
    
    Category of issue: {request.category}
    State: {request.state}
    City: {request.city}
    Pincode: {request.pincode or 'Not provided'}
    
    CRITICAL INSTRUCTIONS:
    1. DO NOT provide generic fallbacks like "Use CPGRAMS" or "Visit portal". You MUST provide REAL phone numbers (e.g., toll-free 1912 for electricity, 155304 for municipal, or specific 10-digit numbers).
    2. Provide a REAL physical address for the local municipal office, ward office, or district collectorate responsible for {request.city}. 
    3. Use your extensive training data to retrieve the exact or closest matching official contact details for {request.state} and {request.city}.
    
    Output strictly in this JSON format:
    {{
        "state": "{request.state}",
        "city": "{request.city}",
        "contacts": [
            {{"office": "Name of office/helpline", "phone": "Phone number", "email": "Email (or NA)", "timings": "Working hours"}}
        ],
        "offices": [
            {{"name": "Name of offline office", "address": "Full physical address", "department": "Department name"}}
        ],
        "alternate_portals": []
    }}
    """
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            tools=[{"type": "web_search"}],
            messages=[
                {"role": "system", "content": "You are a helpful civic assistant. Search the web to find the EXACT real numbers and addresses. Output only valid JSON matching the requested structure."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error fetching local help from OpenAI: {e}")
        return {
            "state": request.state,
            "city": request.city,
            "contacts": [{"office": "State Helpline", "phone": "Use CPGRAMS", "email": "NA", "timings": "Visit portal"}],
            "offices": [{"name": "District Collector Office", "address": f"Contact local district office in {request.city}", "department": "General Administration"}],
            "alternate_portals": []
        }

@api_router.post("/portal/suggest")
async def suggest_portal(request: PortalSuggestionRequest, user: dict = Depends(get_current_user)):
    prompt = f"""
    You are an expert civic assistant for India with deep knowledge of state-level grievance portals (e.g., Aaple Sarkar in Maharashtra, CM Helpline in MP, e-NagarSewa, etc.).
    The user needs to file a formal complaint online.
    
    Category of issue: {request.category}
    State: {request.state}
    City: {request.city}
    Pincode: {request.pincode or 'Not provided'}
    
    CRITICAL INSTRUCTIONS:
    1. DO NOT suggest the national CPGRAMS portal UNLESS there is absolutely no state-level or municipal-level portal available.
    2. Prioritize the specific Municipal Corporation website for {request.city} or the official State Government Grievance Portal for {request.state}.
    3. Provide the REAL URL for the state/local portal.
    
    Output strictly in this JSON format matching the 'Portal' schema:
    {{
        "name": "Portal Name (e.g., CPGRAMS, BMC Grievance)",
        "description": "Short description of the portal",
        "url": "https://official-portal-url.gov.in",
        "guidance_steps": [
            "Step 1: ...",
            "Step 2: ..."
        ]
    }}
    """
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            tools=[{"type": "web_search"}],
            messages=[
                {"role": "system", "content": "You are a helpful civic assistant. Search the web to find the EXACT real state portals. Output only valid JSON matching the requested structure."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error fetching portal suggestion from OpenAI: {e}")
        return {
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

@api_router.post("/contact")
@limiter.limit("3/minute")
async def submit_contact(request: Request, message: ContactMessage):
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
    allow_origins=os.environ['CORS_ORIGINS'].split(','),  # MUST be explicitly configured
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
    # Create indexes for fast auth lookups (idempotent — safe to run every startup)
    await db.users.create_index("email", unique=True, background=True)
    await db.users.create_index("id", unique=True, background=True)
    await db.complaints.create_index("user_id", background=True)
    logger.info("Database indexes ensured")

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
