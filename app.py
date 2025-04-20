from flask import Flask, request, jsonify, render_template
import pandas as pd
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
import json
import requests
from concurrent.futures import ThreadPoolExecutor
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY not set in environment variables")

genai.configure(api_key=api_key)

# Load the SHL assessment data
try:
    df = pd.read_csv('shl_assessments.csv')
    logger.info(f"Loaded {len(df)} assessments from CSV")
except Exception as e:
    logger.error(f"Failed to load assessment data: {str(e)}")
    df = pd.DataFrame()  # Empty dataframe as fallback

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

def extract_text_from_url(url):
    """Extracts text content from a given URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        # This is a simple extraction; in a real implementation, 
        # you might want to use BeautifulSoup for better HTML parsing
        text = re.sub(r'<[^>]+>', ' ', response.text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from URL {url}: {str(e)}")
        return None

def get_recommendations(query, max_results=10):
    """Get assessment recommendations using Gemini API and save to JSON file."""
    try:
        # Construct the prompt with all assessment information
        assessments_info = df.to_dict(orient='records')
        
        prompt = f"""
        You are an expert SHL Assessment recommendation system. Based on the following job description or query, 
        recommend the most relevant SHL assessments from the provided list only. Return your response as a JSON array of objects.

        Here are the available SHL assessments:
        {json.dumps(assessments_info, indent=2)}

        Query: {query}

        Return a JSON array with up to {max_results} most relevant assessments. 
        Each assessment in your response should include these fields:
        - name: The assessment name
        - url: The URL to the assessment
        - description: simply copy-paste from the csv file
        - duration: The duration of the assessment
        - remote_testing: Whether remote testing is supported (Yes/No)
        - adaptive_support: Whether Adaptive/IRT is supported (Yes/No)
        - test_type: The type of the test
        - reason: short explanation of that particular test getting shortlisted

        Format your response as a valid JSON array with no additional text.
        """

        # Get response from Gemini
        response = model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON content from response
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```|```\s*([\s\S]*?)\s*```|([\[\{][\s\S]*?[\]\}])', response_text)
        if json_match:
            json_str = next(group for group in json_match.groups() if group is not None)
            recommendations = json.loads(json_str)
        else:
            recommendations = json.loads(response_text)
        
        # Limit results
        if len(recommendations) > max_results:
            recommendations = recommendations[:max_results]

        # Ensure all required fields exist
        required_fields = ['name', 'url', 'description', 'duration', 'remote_testing', 'adaptive_support', 'test_type']
        for rec in recommendations:
            for field in required_fields:
                if field not in rec:
                    rec[field] = "N/A"

        # Save to recommend.json
        with open("recommend.json", "w", encoding="utf-8") as f:
            json.dump(recommendations, f, indent=2)

        return recommendations
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return []

@app.route('/', methods=['GET'])
def index():
    """Render the home page"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy"
    })

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    """Assessment recommendation endpoint"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        query = data.get('query', '')
        url = data.get('url', '')
        
        # If URL is provided, extract text from it
        if url and not query:
            extracted_text = extract_text_from_url(url)
            if extracted_text:
                query = extracted_text
            else:
                return jsonify({"error": "Failed to extract text from URL"}), 400
                
        if not query:
            return jsonify({"error": "Either query or valid URL must be provided"}), 400
            
        # Get recommendations
        recommendations = get_recommendations(query)
        
        # Simply return the query and the contents of recommendedTests.json
        try:
            with open("recommendedTests.json", "r", encoding="utf-8") as f:
                json_content = json.load(f)
                
            return jsonify({
                "query": query,
                "recommended_assessments": json_content
            })
        except Exception as e:
            # If file doesn't exist yet, return just the recommendations
            return jsonify({
                "query": query,
                "recommended_assessments": recommendations
            })
        
    except Exception as e:
        logger.error(f"Error in recommendation endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))