from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
import mysql.connector
import smtplib
from email.message import EmailMessage

app = FastAPI()

# ================= DATABASE =================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="La_12122005",
        database="mydb"
    )

# ================= JWT =================
SECRET_KEY = "OD_SECRET_KEY"
ALGORITHM = "HS256"
security = HTTPBearer()

def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def require_role(role: str):
    def checker(credentials: HTTPAuthorizationCredentials = Security(security)):
        try:
            payload = decode_token(credentials.credentials)
            if payload["role"] != role:
                raise HTTPException(status_code=403, detail="Access denied")
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    return checker

# ================= MODELS =================
class LoginRequest(BaseModel):
    username: str
    password: str

class ODRequest(BaseModel):
    od_date: str
    duration: str
    reason: str

class ActionRequest(BaseModel):
    od_id: int
    remarks: str = ""

# ================= EMAIL CONFIG =================
EMAIL_ID = "srmod.system@gmail.com"
EMAIL_PASSWORD = "lxtp qoej faew poqo"

def send_email(to_email, subject, body):
    if not to_email:
        return
    msg = EmailMessage()
    msg["From"] = EMAIL_ID
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ID, EMAIL_PASSWORD)
        server.send_message(msg)

def get_student_email(reg_no):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT email FROM students WHERE reg_no=%s", (reg_no,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def get_role_email(role):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE role=%s LIMIT 1", (role,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

# ================= LOGIN =================
@app.post("/login")
def login(data: LoginRequest):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                (data.username, data.password))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "username": user["username"],
        "role": user["role"],
        "reg_no": user["reg_no"]
    })
    return {"access_token": token, "role": user["role"]}

# ================= STUDENT =================
@app.post("/od/request")
def submit_od(req: ODRequest, user=Depends(require_role("STUDENT"))):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO od_requests (reg_no, od_date, duration, reason, status)
        VALUES (%s,%s,%s,%s,'PENDING_TEACHER')
    """, (user["reg_no"], req.od_date, req.duration, req.reason))
    conn.commit()
    cur.close()
    conn.close()

    send_email(get_role_email("TEACHER"), "New OD Request",
               f"New OD submitted by {user['reg_no']}")
    return {"message": "OD submitted"}

@app.get("/od/student")
def student_ods(user=Depends(require_role("STUDENT"))):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id AS od_id, od_date, duration, reason, status
        FROM od_requests WHERE reg_no=%s ORDER BY id DESC
    """, (user["reg_no"],))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# ================= TEACHER =================
@app.get("/od/teacher")
def teacher_pending(user=Depends(require_role("TEACHER"))):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id AS od_id, reg_no, od_date, duration, reason
        FROM od_requests WHERE status='PENDING_TEACHER'
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.post("/teacher/approve")
def teacher_approve(req: ActionRequest, user=Depends(require_role("TEACHER"))):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT reg_no FROM od_requests WHERE id=%s", (req.od_id,))
    reg_no = cur.fetchone()[0]

    cur.execute("UPDATE od_requests SET status='PENDING_HOD' WHERE id=%s", (req.od_id,))
    cur.execute("INSERT INTO od_approvals (od_id, role, decision, remarks) VALUES (%s,'TEACHER','APPROVED',%s)",
                (req.od_id, req.remarks))
    conn.commit()
    cur.close()
    conn.close()

    send_email(get_student_email(reg_no), "OD Approved by Teacher", f"OD ID {req.od_id} approved.")
    send_email(get_role_email("HOD"), "OD Awaiting Approval", f"OD ID {req.od_id} needs approval.")
    return {"message": "Approved by Teacher"}

@app.post("/teacher/reject")
def teacher_reject(req: ActionRequest, user=Depends(require_role("TEACHER"))):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT reg_no FROM od_requests WHERE id=%s", (req.od_id,))
    reg_no = cur.fetchone()[0]

    cur.execute("UPDATE od_requests SET status='REJECTED' WHERE id=%s", (req.od_id,))
    cur.execute("INSERT INTO od_approvals (od_id, role, decision, remarks) VALUES (%s,'TEACHER','REJECTED',%s)",
                (req.od_id, req.remarks))
    conn.commit()
    cur.close()
    conn.close()

    send_email(get_student_email(reg_no), "OD Rejected by Teacher", f"Remarks:\n{req.remarks}")
    return {"message": "Rejected by Teacher"}

# ================= HOD =================
@app.get("/od/hod")
def hod_pending(user=Depends(require_role("HOD"))):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id AS od_id, reg_no, od_date, duration, reason
        FROM od_requests WHERE status='PENDING_HOD' ORDER BY id DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.post("/hod/approve")
def hod_approve(req: ActionRequest, user=Depends(require_role("HOD"))):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT reg_no FROM od_requests WHERE id=%s", (req.od_id,))
    reg_no = cur.fetchone()[0]

    cur.execute("UPDATE od_requests SET status='PENDING_DEAN' WHERE id=%s", (req.od_id,))
    cur.execute("INSERT INTO od_approvals VALUES (NULL,%s,'HOD','APPROVED',%s,NOW())",
                (req.od_id, req.remarks))
    conn.commit()
    cur.close()
    conn.close()

    send_email(get_student_email(reg_no), "OD Approved by HOD", f"OD ID {req.od_id} approved.")
    send_email(get_role_email("DEAN"), "OD Awaiting Approval", f"OD ID {req.od_id} needs approval.")
    return {"message": "Approved by HOD"}

@app.post("/hod/reject")
def hod_reject(req: ActionRequest, user=Depends(require_role("HOD"))):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT reg_no FROM od_requests WHERE id=%s", (req.od_id,))
    reg_no = cur.fetchone()[0]

    cur.execute("UPDATE od_requests SET status='REJECTED' WHERE id=%s", (req.od_id,))
    cur.execute("INSERT INTO od_approvals VALUES (NULL,%s,'HOD','REJECTED',%s,NOW())",
                (req.od_id, req.remarks))
    conn.commit()
    cur.close()
    conn.close()

    send_email(get_student_email(reg_no), "OD Rejected by HOD", f"Remarks:\n{req.remarks}")
    return {"message": "Rejected by HOD"}

# ================= DEAN =================
@app.get("/od/dean")
def dean_pending(user=Depends(require_role("DEAN"))):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id AS od_id, reg_no, od_date, duration, reason
        FROM od_requests WHERE status='PENDING_DEAN' ORDER BY id DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.post("/dean/approve")
def dean_approve(req: ActionRequest, user=Depends(require_role("DEAN"))):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT reg_no FROM od_requests WHERE id=%s", (req.od_id,))
    reg_no = cur.fetchone()[0]

    cur.execute("UPDATE od_requests SET status='APPROVED' WHERE id=%s", (req.od_id,))
    cur.execute("INSERT INTO od_approvals VALUES (NULL,%s,'DEAN','APPROVED',%s,NOW())",
                (req.od_id, req.remarks))
    conn.commit()
    cur.close()
    conn.close()

    send_email(get_student_email(reg_no), "OD Fully Approved", "Your OD is approved.")
    return {"message": "OD fully approved"}

@app.post("/dean/reject")
def dean_reject(req: ActionRequest, user=Depends(require_role("DEAN"))):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT reg_no FROM od_requests WHERE id=%s", (req.od_id,))
    reg_no = cur.fetchone()[0]

    cur.execute("UPDATE od_requests SET status='REJECTED' WHERE id=%s", (req.od_id,))
    cur.execute("INSERT INTO od_approvals VALUES (NULL,%s,'DEAN','REJECTED',%s,NOW())",
                (req.od_id, req.remarks))
    conn.commit()
    cur.close()
    conn.close()

    send_email(get_student_email(reg_no), "OD Rejected by Dean", f"Remarks:\n{req.remarks}")
    return {"message": "Rejected by Dean"}
