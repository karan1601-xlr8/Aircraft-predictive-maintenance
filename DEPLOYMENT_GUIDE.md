# 🚀 Streamlit App Deployment Guide

## Quick Start (Local Testing)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🌐 Deploy to Streamlit Cloud (FREE!)

### Step 1: Prepare Your Repository

1. **Create GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Predictive Maintenance Streamlit App"
   ```

2. **Push to GitHub**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/predictive-maintenance-app.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)

2. Click **"New app"**

3. Fill in details:
   - **Repository**: `YOUR_USERNAME/predictive-maintenance-app`
   - **Branch**: `main`
   - **Main file path**: `app.py`

4. Click **"Deploy!"**

5. Wait 2-5 minutes for deployment

6. Your app will be live at: `https://YOUR_APP_NAME.streamlit.app` 🎉

---

## 📁 Required File Structure

```
predictive-maintenance-app/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── src/
│   ├── __init__.py
│   └── inference.py       # Prediction logic
├── README.md              # This file
└── .gitignore             # Git ignore file
```

---

## 🔧 Configuration Options

### Custom Theme (Optional)
Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor="#1f77b4"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#262730"
font="sans serif"
```

### Secrets Management (For Production)
If using real models, add secrets in Streamlit Cloud:

1. Go to app settings
2. Click "Secrets"
3. Add:
```toml
# .streamlit/secrets.toml
model_path = "path/to/your/model"
api_key = "your-api-key"
```

---

## 🐛 Troubleshooting

### Issue: "Module not found"
**Solution**: Ensure all dependencies are in `requirements.txt`

### Issue: "Port already in use"
**Solution**: 
```bash
# Kill the process
pkill -f streamlit
# Or use a different port
streamlit run app.py --server.port 8502
```

### Issue: "Memory limit exceeded" on Streamlit Cloud
**Solution**: 
- Optimize data loading
- Use caching with `@st.cache_data`
- Consider upgrading to Streamlit Teams

---

## 🎨 Customization Ideas

### 1. Add Real Model Integration
Replace the demo prediction logic in `src/inference.py` with your trained LSTM model:

```python
import tensorflow as tf

class PredictiveMaintenanceModel:
    def __init__(self):
        self.model = tf.keras.models.load_model('models/lstm_model.keras')
        self.scaler = pickle.load(open('models/scaler.pkl', 'rb'))
```

### 2. Add Authentication
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(...)
name, authentication_status, username = authenticator.login('Login', 'main')
```

### 3. Add Database Integration
```python
import sqlite3

def save_prediction(result):
    conn = sqlite3.connect('predictions.db')
    # Save to database
```

### 4. Add Email Alerts
```python
import smtplib

def send_alert(rul):
    if rul < 30:
        # Send email to maintenance team
```

---

## 📊 Performance Tips

1. **Use Caching**:
```python
@st.cache_data
def load_data(file):
    return pd.read_csv(file)
```

2. **Lazy Loading**:
   - Don't load models until needed
   - Use session state for persistence

3. **Optimize Images**:
   - Compress images before uploading
   - Use appropriate formats (PNG for graphics, JPG for photos)

---

## 🔒 Security Best Practices

1. **Never commit secrets**:
   - Add `.streamlit/secrets.toml` to `.gitignore`
   - Use environment variables

2. **Validate user input**:
   - Check file sizes
   - Validate CSV structure
   - Sanitize inputs

3. **Rate limiting**:
   - Limit prediction frequency
   - Add cooldown periods

---

## 📈 Next Steps

1. ✅ Test locally
2. ✅ Deploy to Streamlit Cloud
3. 📝 Add to your resume/LinkedIn
4. 🎥 Record a demo video
5. 📱 Share with potential employers

---

## 🆘 Support

- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Community Forum**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues**: Create issue in your repo

---

## 📄 License

MIT License - Feel free to use for portfolio projects!

---

## 🎓 Learn More

- [Streamlit Gallery](https://streamlit.io/gallery)
- [Streamlit Components](https://streamlit.io/components)
- [Advanced Features](https://docs.streamlit.io/library/advanced-features)
