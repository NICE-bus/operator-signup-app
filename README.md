# Driver Signup App

A tablet-friendly Streamlit application to replace physical clipboards for driver work signups.

## 🚀 Live Demo

**[Access the app here](https://your-app-name.streamlit.app)** *(Update this after deployment)*

## Features

- **4 Clipboard Types**: RDO, AM Spare, PM Spare, Extra Work
- **Multi-day Signup**: Shows next 7 days for signup
- **Touch-friendly Interface**: Large buttons optimized for tablets
- **Real-time Updates**: See current signups immediately
- **File-based Storage**: Simple JSON files for data persistence
- **No Authentication**: Open access for all drivers

## Quick Start

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   streamlit run app.py
   ```

3. Open in browser and navigate to the tablet

### Streamlit Cloud Deployment

This app is deployed on Streamlit Cloud. Any changes pushed to the main branch will automatically deploy.

## Usage Flow

1. **Select Clipboard** → Choose from 4 signup types
2. **Select Date** → Pick from next 7 days  
3. **Sign Up** → Enter name and any notes
4. **Confirmation** → See success message and updated list

## Data Storage

- Signup data stored in `signup_data/` folder
- One JSON file per clipboard type per date
- Format: `{clipboard_type}_{YYYY-MM-DD}.json`
- **Note**: Data persists between deployments on Streamlit Cloud

## Customization

- Modify clipboard types in the main app
- Add additional form fields for specific signup requirements
- Customize styling in the CSS section
- Add supervisor features in the sidebar

## For TRANSDEV Team

- **Access URL**: Share the Streamlit Cloud URL with all drivers
- **Tablet Setup**: Bookmark the URL on all tablets
- **Data Management**: Supervisor tools available in sidebar

## Support

Questions? Contact your supervisor or IT support.