# shl-assessment-recommender-using-webscraping-geminiAPI-flask-GCP

A simple yet powerful web app that lets users query and search for SHL assessments based on natural language inputs. The app uses **Google's Gemini API** to understand user queries and fetch relevant assessment details from a **CSV file**. Built with **Flask** as the backend, and a clean **HTML/CSS frontend**, this project integrates Google Cloud services like **GCS** and **Compute Engine VM** for deployment.

---

## 🧠 How It Works

- A `shl_assessments.csv` file contains a curated list of SHL assessments, including titles, categories, descriptions, and other metadata.
- Two Python scripts—`dataScraper_individualTestSolutions.py` and `dataScraper_prepackagedJobSolutions.py`—are used to **scrape structured assessment data** from official sources and populate the CSV.
- The user submits a **natural language query** through the frontend interface located at `templates/index.html` (e.g., _"Give me a Python programming test"_).
- The backend Flask server (`app.py`) receives this input and sends the query to the **Gemini API** to interpret the user's intent.
- The app uses the Gemini output to **match the most relevant assessments** from the CSV dataset.
- The matched assessments are:
  - **Stored in `recommend.json`**, which acts as a temporary storage of results for further use or analysis.
  - **Displayed dynamically on the frontend** so the user receives real-time feedback and recommendations.
- A `requirements.txt` file is included in the project root, listing all necessary Python dependencies for smooth environment setup.

---

## 🛠 Tech Stack

| Component        | Description                                |
|------------------|--------------------------------------------|
| `Flask`          | Backend server handling routes and logic   |
| `HTML/CSS/JS`    | Frontend UI via `index.html`               |
| `CSV File`       | Local database of assessments              |
| `Gemini API`     | For NLP and query understanding            |
| `Google Cloud`   | VM + Bucket for deployment                 |

---

## 📁 Project Structure


---

## 🚀 Setup Instructions

### ✅ Prerequisites

- Python 3.8+
- Google Cloud Project with:
  - Gemini API / Vertex AI enabled
  - GCS bucket for file storage
  - VM instance (Ubuntu recommended)

---

### 📦 Install Dependencies

1. **Clone the Repository**

```bash
git clone https://github.com/your-username/shl-assessment-gemini.git
cd shl-assessment-gemini
```

2. **Set Up a Virtual Environment**
```
python3 -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activat
```

3. **Install Python Dependencies**
Create a file named .env in the root of the project:
```
pip install -r requirements.txt
```

4. **Set Up Gemini API Access**
Create a file named .env in the root of the project:
```
touch .env
```
Add your API key to the .env file:
```
GEMINI_API_KEY=your_actual_api_key
```
In app.py, make sure you're loading it:
```
from dotenv import load_dotenv
load_dotenv()
import os
api_key = os.getenv("GEMINI_API_KEY")
```

5. **Run the App Locally**
Inside your virtual environment, start the Flask server
```
python app.py
```
By default, Flask runs on port 5000. You should see output like:
```
Running on http://127.0.0.1:5000/
```
Open your browser and visit:
```
http://localhost:5000
```
You’ll see your web app in action!
