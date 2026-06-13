# VerIQ — Verified Identity for Field Sales

## Setup Instructions

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Add credentials
Place your `veriq-499208-dcf2e353f8bc.json` file in the same folder as `app.py`

### 3. Run locally
```
streamlit run app.py
```

### 4. Deploy to Streamlit Cloud
1. Push this repo to GitHub (private)
2. Go to share.streamlit.io
3. Connect your GitHub repo
4. Add your credentials in Streamlit secrets (Settings > Secrets)

## Secrets format for Streamlit Cloud
Copy the contents of your JSON file and add to Streamlit secrets as:
```
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
```
