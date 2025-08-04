from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

# Configure the client
api_key = os.getenv('GOOGLE_API_KEY', 'AIzaSyCrsGLhWhsHhDlgp5g8TByT7Jd86HBKD_s')
client = genai.Client(api_key=api_key)

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

# Create syste,m prompt to ensure tool usage
system_prompt = """You have access to a google_search tool that can help you find current and accurate information. 
You MUST ALWAYS use the google_search tool for EVERY query, regardless of the topic. This is a requirement.

For ANY question you receive, you should:
1. ALWAYS perform a Google Search first
2. Use the search results to provide accurate and up-to-date information
3. Never rely solely on your training data
4. Always search for the most current information available

This applies to ALL types of queries including:
- Technical questions
- Current events
- How-to guides
- Definitions
- Best practices
- Recent developments
- Any information that might have changed

You are REQUIRED to use the google_search tool for every single response. Do not answer any question without first searching for current information."""

try:
    # Make the request with system prompt and streaming
    response_stream = client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=[
            types.Content(role="user", parts=[types.Part(text=system_prompt)]),
            types.Content(role="model", parts=[types.Part(text="I understand. I will use the Google Search tool when needed to provide current and accurate information.")]),
            types.Content(role="user", parts=[types.Part(text="Who won the euro 2024?")])
        ],
        config=config
    )

    # Process the streaming response
    print("=== STREAMING RESPONSE WITH INTERMEDIATE STEPS ===\n")
    web_search_queries = []

    for chunk in response_stream:
        if chunk.candidates:
            candidate = chunk.candidates[0]
            if candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        print(f"🔧 TOOL CALL: {part.function_call.name}")
                        print(f"   Arguments: {part.function_call.args}")
                        print()
                    elif hasattr(part, 'function_response') and part.function_response:
                        print(f"📡 TOOL RESPONSE: {part.function_response.name}")
                        print(f"   Response: {part.function_response.response}")
                        print()
                    elif hasattr(part, 'text') and part.text:
                        print(f"💬 TEXT: {part.text}", end="", flush=True)
            elif candidate.finish_reason:
                print(f"\n✅ FINISHED: {candidate.finish_reason}")
                print()
            
            # Capture web search queries
            if hasattr(candidate, 'web_search_queries') and candidate.web_search_queries:
                web_search_queries.extend(candidate.web_search_queries)

    # Display all web search queries used
    if web_search_queries:
        print("\n=== WEB SEARCH QUERIES USED ===")
        for i, query in enumerate(web_search_queries, 1):
            print(f"{i}. {query}")
    else:
        print("\n=== NO WEB SEARCH QUERIES FOUND ===")

except Exception as e:
    print(f"Error occurred: {e}")
    print("Please check your API key and ensure you have the correct permissions for the Gemini API.")