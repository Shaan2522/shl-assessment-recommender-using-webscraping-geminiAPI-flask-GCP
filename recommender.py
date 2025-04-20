from google import genai
import pandas as pd
import os
from dotenv import load_dotenv
from google import generativeai

# Load environment variables
load_dotenv()

# Set up Gemini API key
api_key = os.getenv('GEMINI_API_KEY')

# Initialize the genai client
client = genai.Client(api_key=api_key)

# Load the SHL assessment data
assessments_data = pd.read_csv('data/shl_assessments.csv')

# Function to call the Gemini API for text generation
def get_gemini_recommendations(query):
    try:
        # Use the Gemini model to generate content based on the query
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Model name as per the API documentation
            contents=query  # The query is passed as the content to be processed
        )
        # Get the response text from Gemini API
        return response.text.strip()
    except Exception as e:
        print(f"Error with Gemini API: {e}")
        return None

# Function to process the query and get recommendations
def get_recommendations(query):
    # Get Gemini recommendations based on the query
    recommendations_text = get_gemini_recommendations(query)
    
    if not recommendations_text:
        return []
    
    # Parse the recommendations text and match with assessments
    recommendations = []
    for assessment_name in assessments_data['Assessment Name']:
        if assessment_name.lower() in recommendations_text.lower():
            # Get assessment details from the dataset
            assessment = assessments_data[assessments_data['Assessment Name'] == assessment_name].iloc[0]
            recommendations.append({
                "name": assessment['Assessment Name'],
                "url": assessment['URL'],
                "remote_testing_support": assessment['Remote Testing Support'],
                "adaptive_support": assessment['Adaptive/IRT Support'],
                "duration": assessment['Duration'],
                "test_type": assessment['Test Type'],
                "submission_materials": assessment['Submission Materials']
            })
    
    # Return at most 10 recommendations
    return recommendations[:10]
