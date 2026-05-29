# Firebase Setup Guide

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
4. Save the JSON file as `firebase-key.json`

## Step 4: Add to Streamlit Cloud

1. Go to your Streamlit Cloud app settings
2. Click "Secrets"
3. Add:
   ```
   FIREBASE_CREDENTIALS = "/mount/src/firebase-key.json"
   ```

## Step 5: Upload Key to GitHub

1. Upload `firebase-key.json` to your GitHub repo (PRIVATE repo recommended!)
2. Add to `.gitignore`:
   ```
   firebase-key.json
   ```

## Step 6: Redeploy

Your app will auto-redeploy and trades will persist across all devices!

---

## For Local Development

Set environment variable:
```bash
set FIREBASE_CREDENTIALS=firebase-key.json
```

Then run:
```bash
python -m streamlit run app.py