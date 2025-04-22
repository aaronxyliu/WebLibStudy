# API: sk-00e65ee6311846f0bdb91c2377f9598f

from openai import OpenAI
from time import sleep
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
db = ConnDatabase('Libraries')
logger = getLogger()


TABLE = 'libs_cdnjs_all_4_20u'
CRAWL_START = 111
CRAWL_INTERVAL = 0.2    # sleep seconds between iterations

# Configuration
DEEPSEEK_API_KEY = "sk-00e65ee6311846f0bdb91c2377f9598f"


# Initialize the OpenAI client configured for Deepseek
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",  # DeepSeek-V3
)

# Function to categorize a library using Deepseek API
def categorize_library(name, url, description):
    prompt = f"""
    Based on the following information about a web library, categorize its primary usage purpose:
    
    Library Name: {name}
    Github URL: {url}
    Description: {description}
    
    Please respond with ONLY the category name (without number) from the following options:
    1. UI Framework (e.g., React, Vue)
    2. UI Component (e.g., twemoji-js, font-awesome)
    3. CSS Framework (e.g., Bootstrap, Tailwind)
    4. State Management (e.g., Redux, MobX)
    5. Routing (e.g., React Router)
    6. HTTP Client (e.g., Axios, Fetch)
    7. Form Handling (e.g., Formik)
    8. Testing (e.g., Jest, Cypress)
    9. Animation (e.g., GSAP, Framer Motion)
    10. Utility (e.g., Lodash, Underscore)
    11. Data Visualization (e.g., D3, Chart.js)
    12. Authentication (e.g., Auth0, Passport)
    13. Other (if none of the above fit)
    
    If uncertain, choose the most likely category.
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # Verify the correct model name
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=20
        )
        category = response.choices[0].message.content.strip()
        return category
    except Exception as e:
        logger.warning(f"Error categorizing {name}: {str(e)}")
        return None

# Main processing function
def process_libraries():
    # Get all libraries that haven't been categorized yet
    # Assuming you have a 'category' column that's NULL for uncategorized libraries
    libraries = db.select_all(TABLE, ['libname', 'github', 'description'])
    
    for lib in libraries:
        libname, url, description = lib['libname'], lib['github'], lib['description']
        
        logger.info(f"Processing: {libname} ({url})")
        
        # Get category from Deepseek API
        category = categorize_library(libname, url, description)
        
        if category:
            # Update the database with the category
            db.update(TABLE, 
                data={'category': category}, 
                condition="`libname`=%s", 
                condition_values=(libname,))

            logger.info(f"Assigned category: {category}")
        else:
            logger.warning("Failed to categorize this library")
        
        # Be kind to the API - add a delay between requests
        sleep(1)  # Adjust based on your API rate limits

if __name__ == "__main__":
    process_libraries()

    db.close()