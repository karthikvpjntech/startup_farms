# Agri-Smart Ecosystem — Cloud & Database Integrations Guide

This guide provides instructions for connecting **Supabase PostgreSQL Database**, **Cloudinary Media Storage**, **Email Notifications**, **SMS Gateways**, and **Razorpay Payment Gateway (Test Mode)**.

---

## 1. 🐘 Supabase PostgreSQL Database Connection

### 1.1 Overview
The Agri-Smart Ecosystem uses SQLAlchemy 2.0 with the modern `psycopg3` driver (`postgresql+psycopg://`). It fully supports Supabase's transaction pooler (port `6543`) and session connection (port `5432`).

### 1.2 Step-by-Step Connection Instructions

1. **Create a Supabase Project**:
   - Log in to [Supabase Dashboard](https://supabase.com/dashboard).
   - Click **New Project** (select your preferred region, e.g. `ap-south-1` Mumbai).
   - Set a strong Database Password and note it down.

2. **Retrieve Connection String**:
   - In your Supabase Project, navigate to: **Project Settings** → **Database** → **Connection String**.
   - Select the **URI** tab.
   - Choose **Transaction Pooler** (recommended for production, Port `6543`):
     ```text
     postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
     ```
   - Alternatively, choose **Session Pooler** (Port `5432`):
     ```text
     postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
     ```

3. **Configure `backend/.env`**:
   Update `DATABASE_URL` in `backend/.env` with your Supabase URI (prefixing with `postgresql+psycopg://`):
   ```env
   DATABASE_URL=postgresql+psycopg://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```

4. **Initialize Schema & Master Taxonomy**:
   Run the following commands in the backend virtual environment:
   ```bash
   cd backend
   .\.venv\Scripts\Activate.ps1

   # 1. Run Alembic schema migrations
   alembic upgrade head

   # 2. Run master seeders (Roles, Super Admin, Crop Stages, Inputs, Suppliers, Livestock Master)
   python -m app.seeds.run_seed
   ```

---

## 2. ☁️ Cloudinary Media Storage Connection

### 2.1 Overview
Cloudinary provides cloud media hosting for high-resolution crop stage inspection photos, livestock verified certificates, farmer profile avatars, and bill proofs.

### 2.2 Setup Instructions

1. Log in to [Cloudinary Console](https://console.cloudinary.com/).
2. On the **Dashboard**, locate your:
   - **Cloud Name** (e.g. `agri-smart-cloud`)
   - **API Key** (e.g. `489123847291823`)
   - **API Secret** (e.g. `aBcdEFG123456789`)
3. Add these credentials to `backend/.env`:
   ```env
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   CLOUDINARY_SECURE=true
   CLOUDINARY_FOLDER=agri_smart
   ```
4. **Local Fallback:** If Cloudinary keys are omitted, the media service automatically saves uploads locally in `backend/uploads/` with zero errors.

---

## 3. 💳 Razorpay Payment Gateway (Test Mode)

### 3.1 Overview
Razorpay processes orders via standard UPI, Credit/Debit Cards, Net Banking, and Digital Wallets.

### 3.2 Setup Test Mode

1. Log in to [Razorpay Dashboard](https://dashboard.razorpay.com/).
2. Toggle the switch at the top to **Test Mode**.
3. Go to **Settings** → **API Keys** → click **Generate Test Key**.
4. Copy the `Key Id` (starts with `rzp_test_...`) and `Key Secret`.
5. Update `backend/.env`:
   ```env
   RAZORPAY_ENABLED=true
   RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID
   RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET
   RAZORPAY_CURRENCY=INR
   ```
6. **Frontend Integration:** When customers checkout at `/checkout` with card or UPI, the official Razorpay Checkout popup appears in test mode. Razorpay test cards (e.g. `4111 1111 1111 1111`, expiry in future, any CVV) or test UPI (`success@razorpay`) can be used for instant simulation.

---

## 4. ✉️ Email Notifications (SMTP / Gmail)

### 4.1 Overview
Sends transactional emails for account creation, order confirmation invoices, digital payment receipts, and delivery dispatch alerts.

### 4.2 Setup with Gmail App Password

1. Enable 2-Step Verification on your Google account.
2. Go to **Google Account** → **Security** → **App Passwords**.
3. Generate a 16-character app password named `AgriSmart`.
4. Update `backend/.env`:
   ```env
   EMAIL_ENABLED=true
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your_email@gmail.com
   SMTP_PASSWORD=your_16_character_app_password
   SMTP_FROM_EMAIL=your_email@gmail.com
   SMTP_FROM_NAME=Agri-Smart Ecosystem
   SMTP_TLS=true
   ```

---

## 5. 📱 SMS & Instant Message Notifications

### 5.1 Overview
Dispatches transactional SMS alerts upon order placement, payment confirmation, and driver dispatch milestones.

### 5.2 Option A: Twilio Gateway
```env
SMS_ENABLED=true
SMS_PROVIDER=TWILIO
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
```

### 5.3 Option B: Fast2SMS (India Routes)
```env
SMS_ENABLED=true
SMS_PROVIDER=FAST2SMS
FAST2SMS_API_KEY=your_fast2sms_api_key
```

### 5.4 Option C: Local Console Simulation (Default)
```env
SMS_ENABLED=false
SMS_PROVIDER=LOG_CONSOLE
```
In this mode, all SMS dispatches are simulated cleanly in application logs and stored in the `sms_logs` database table for auditing.

---

## 6. 🛡️ Verification & Health Checklist

To verify all services:
```bash
# Check backend health
curl http://127.0.0.1:8000/api/v1/health

# Verify clean database state (1 user = Super Admin)
python -m app.seeds.clean_mock_data
```
