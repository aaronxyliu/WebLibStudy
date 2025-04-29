# Use LLM to categorize libraries
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
    
    Here is the converted content in the requested format:

    1. UI Framework (Comprehensive tools for building structured user interfaces. e.g., React, Vue.js, Angular, Svelte)  
    2. Framework Extension (Plugins that enhance UI frameworks with extra features. e.g., Redux Toolkit, Vuex, NgRx)  
    3. UI Component (Pre-built UI components for faster development. e.g., Material-UI, Element UI, Bootstrap, Chakra UI)  
    4. DOM Manipulation (Simplify DOM interaction and event handling. e.g., jQuery, Umbrella JS, Cash)  
    5. Icons & Fonts (Scalable vector assets. e.g., Font Awesome, Twemoji, Iconify)  
    6. Routing (Client-side navigation and URL management. e.g., React Router, Vue Router, Angular Router)  
    7. Internationalization (For translation and locale formatting. e.g., babelfish, ng-i18next)  
    8. Code Utilities (Lightweight helpers for common programming tasks. e.g., Lodash, Ramda, Moment.js)  
    9. Module/Bundling (Code organization and optimization. e.g., Webpack, Rollup, Vite, CommonJS/ES Modules)  
    10. Performance (High-performance computing (WASM) and performance optimization tools. e.g., Emscripten, LazyLoader, WASM-focused libs)  
    11. Data Storage (Client-side storage solutions. e.g., RxDB, lowdb, localForage, IndexedDB wrappers)  
    12. API/Communication (HTTP clients, real-time communication, and form handling. e.g., Axios, Fetch API, GraphQL clients (Apollo), Socket.IO)  
    13. Document Processing (Parse, generate, manipulate, or present documentation. e.g., impress.js, docsify)  
    14. Graphics & Animation (General-purpose rendering, motion, and effects. e.g., Three.js, GSAP, Anime.js, PixiJS)  
    15. Data Visualization (Charts, graphs, and dashboards. e.g., D3.js, Chart.js, Highcharts, ECharts)  
    16. Multimedia (Image, audio, or video manipulation and playback. e.g., Howler.js, Tone.js, Video.js)  
    17. Game Development (Engines and frameworks for browser games. e.g., Phaser, Babylon.js, MelonJS, p5.js)  
    18. Testing (Tools for quality assurance and environmental checks. e.g., Jest, Vitest, Cypress, adblock-detect)  
    19. Debugging & Profiling (Diagnose performance/issues. e.g., React DevTools, Redux DevTools, Lighthouse)  
    20. Authentication/Authorization (User security and access control. e.g., Auth0, Passport.js, Firebase Auth)  
    21. Cryptography (Encryption/hashing in the browser. e.g., crypto-js, Web Crypto API, libsodium)  
    22. Sanitizer (Prevent security attacks. e.g., validator, js-xss)  
    23. AI (Machine learning models. e.g., TensorFlow.js, Brain.js, ONNX.js)
    24. Other

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
    db.add_column(TABLE, "category", "varchar(100)", after_column='libname')
    libraries = db.select_all(TABLE, ['libname', 'github', 'description'])
    
    i = 1
    for lib in libraries:
        libname, url, description = lib['libname'], lib['github'], lib['description']
        
        logger.info(f"Processing: ({i}/{len(libraries)}) {libname} ({url})")
        
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

        logger.leftTimeEstimator(len(libraries) - i)
        i += 1

if __name__ == "__main__":
    process_libraries()

    db.close()