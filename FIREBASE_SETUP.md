# Firebase Setup Guide (SECURE VERSION)

## ⚠️ IMPORTANT: Never upload service account keys to public repos!

### Secure Approach: Use Streamlit Secrets

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Name it "stock-trader-db"
4. Disable Google Analytics (not needed)
5. Click "Create project"

## Step 2: Enable Firestore Database

1. In Firebase Console, go to "Build" → "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode"
4. Select a location (nearest to you)
5. Click "Done"

## Step 3: Get Service Account Key

1. Go to Project Settings (gear icon)
2. Click "Service accounts"
3. Click "Generate new private key"
4. **COPY the entire JSON content** (don't download!)

## Step 4: Add to Streamlit Cloud Secrets

1. Go to your Streamlit Cloud app settings
2. Click "Secrets"
3. Add the JSON content as a secret:
   ```
   FIREBASE_CREDENTIALS = {"type": "service_account", "project_id": "...", ...}
   ```
   (Paste the entire JSON from Step 3)

## Step 5: Redeploy

Your app will auto-redeploy and trades will persist across all devices!

---

## For Local Development

1. Save the JSON file locally (KEEP IT PRIVATE!)
2. Set environment variable:
   ```bash
   set FIREBASE_CREDENTIALS=firebase-key.json
   ```
3. Run:
   ```bash
   python -m streamlit run app.py
   ```

---

## Security Notes:
- ✅ Streamlit Secrets are encrypted
- ✅ Never commit keys to GitHub
- ✅ Keep local JSON file in a secure location
- ✅ Firebase Console shows who accessed your project