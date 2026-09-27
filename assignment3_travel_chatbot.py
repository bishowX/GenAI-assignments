import logging
import os

import gradio as gr
import requests

from dotenv import load_dotenv
load_dotenv()

from strands import Agent, tool
from strands.models.openai import OpenAIModel
from strands.tools.executors import SequentialToolExecutor
from tavily import TavilyClient

# Strands logs a warning on every turn because gpt-oss returns reasoning text. It's harmless.
logging.getLogger("strands.models.openai").setLevel(logging.ERROR)

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# -----------------------------
# 1. Define tools
# -----------------------------

@tool
def get_weather(city: str) -> dict:
    """Get the current weather for a city from OpenWeather.

    Args:
        city: Name of the city (e.g., "Kathmandu").
    """
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": os.getenv("OPENWEATHER_API_KEY"), "units": "metric"},
            timeout=10,
        )
    except requests.RequestException as e:
        # Don't return str(e). It contains the request URL, and the URL has the API key.
        return {"error": f"Could not reach OpenWeather ({type(e).__name__})."}

    if response.status_code != 200:
        return {"error": f"OpenWeather returned {response.status_code} for '{city}'."}

    data = response.json()
    return {
        "city": data["name"],
        "temperature_c": data["main"]["temp"],
        "description": data["weather"][0]["description"],
    }


@tool
def search_attractions(city: str) -> dict:
    """Search the web for popular tourist attractions and their entry fees in a city.

    Args:
        city: Name of the city (e.g., "Kathmandu").
    """
    try:
        response = tavily_client.search(
            query=f"top 3 tourist attractions in {city} with entry ticket price",
            search_depth="basic",
            max_results=3,
        )
    except Exception as e:
        return {"error": f"Search failed: {e}"}

    return {
        "results": [
            {"title": r.get("title"), "content": r.get("content"), "url": r.get("url")}
            for r in response.get("results", [])
        ]
    }


@tool
def calculate_total_cost(costs: list[float]) -> dict:
    """Add up a list of costs (e.g., entry fees in USD) and return the total.

    Args:
        costs: The individual costs to add, e.g. [10.0, 5.5, 0].
    """
    return {"costs": costs, "total": round(sum(costs), 2)}


# -----------------------------
# 2. Initialize model
# -----------------------------

model = OpenAIModel(
    model_id="openai/gpt-oss-120b",
    client_args={
        "api_key": os.getenv("GROQ_API_KEY"),
        "base_url": "https://api.groq.com/openai/v1"
    }
)


# -----------------------------
# 3. Create Strands Agent
# -----------------------------

SYSTEM_PROMPT = """You are a friendly travel planner chatbot that builds one-day itineraries.
When the user names a city:
1. Call get_weather for the current weather.
2. Call search_attractions and pick 3 popular attractions. Estimate each one's entry fee
   in USD from the search results (use 0 if it is free; say when a price is an estimate).
3. Call calculate_total_cost with the 3 fees. Never add the numbers yourself.
4. Reply in Markdown with:
   - **Weather:** a short summary and a tip based on it
   - **Itinerary:** Morning / Afternoon / Evening, one attraction each, with its fee
   - **Total estimated cost:** the total from calculate_total_cost
If the user hasn't named a city yet, ask which city they want to visit.
If a tool returns an error, say so briefly and continue with what you have."""

# One agent serves every browser tab, so all chats share the same memory.
# That's fine for running it locally.
agent = Agent(
    model=model,
    tools=[get_weather, search_attractions, calculate_total_cost],
    tool_executor=SequentialToolExecutor(),
    system_prompt=SYSTEM_PROMPT,
    callback_handler=None,  # don't print the model's reasoning in the terminal
)


# -----------------------------
# 4. Chat function
# -----------------------------

def chat(message, history):
    try:
        return str(agent(message))
    except Exception as e:
        return f"Sorry, something went wrong while planning your trip: {e}"


# -----------------------------
# 5. Gradio UI
# -----------------------------

gr.ChatInterface(
    fn=chat,
    title="🧳 One-Day Travel Planner",
    description="Tell me a city and I'll check the weather, find 3 attractions, and estimate the cost.",
    examples=["Kathmandu", "Paris", "Plan a day in Tokyo"],
).launch()
