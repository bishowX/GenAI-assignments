# GenAI assignments

My solutions to the three GenAI assignments.

| File | Assignment | Uses |
|---|---|---|
| [`assignment1_weather_agent.ipynb`](assignment1_weather_agent.ipynb) | 1. Weather agent. Gets the weather for 3 cities one at a time and averages the temperature. | Gemini, OpenWeather |
| [`assignment2_travel_planner.ipynb`](assignment2_travel_planner.ipynb) | 2. Travel planner. Makes a one-day plan from the weather, 3 attractions and their total cost. | Strands, Groq, Tavily, OpenWeather |
| [`assignment3_travel_chatbot.py`](assignment3_travel_chatbot.py) | 3. Travel planner chatbot. Assignment 2 as a Gradio chat app. | Strands, Groq, Tavily, OpenWeather, Gradio |

The notebooks are saved with their outputs, so you can see the results without running anything.

## Setup

You need Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

Then put your API keys in `.env`:

| Variable | Needed for | Get one at |
|---|---|---|
| `GEMINI_API_KEY` | 1 | https://aistudio.google.com/apikey |
| `GROQ_API_KEY` | 2, 3 | https://console.groq.com/keys |
| `TAVILY_API_KEY` | 2, 3 | https://app.tavily.com |
| `OPENWEATHER_API_KEY` | 1, 2, 3 | https://home.openweathermap.org/api_keys |

A new OpenWeather key can take up to 2 hours to start working. Until then it returns "Invalid API key".

## Running

For the notebooks, run `jupyter lab`, open a notebook and choose Run → Run All Cells.

For the chatbot, run `python assignment3_travel_chatbot.py`, open http://127.0.0.1:7860 and type a city name.

## How it works

### Assignment 1

Gemini has one tool, `get_current_weather`, which calls OpenWeather. I turned off Gemini's automatic function calling and wrote the loop myself. Each tool call runs in order, and each step is printed. The average is calculated in Python from the temperatures the tool returned, so it doesn't depend on the model doing the math. If a city fails, the notebook prints the error and skips the average.

### Assignments 2 and 3

A Strands agent has three tools, and `SequentialToolExecutor` runs them one at a time:

- `get_weather(city)` gets the current weather from OpenWeather.
- `search_attractions(city)` searches Tavily for popular attractions and their entry fees.
- `calculate_total_cost(costs)` adds up the fees.

The model picks 3 attractions, estimates each entry fee in USD from the search results, and uses the calculator tool for the total. The reply is a morning, afternoon and evening plan with a weather tip.

The entry fees are estimates from web search results. The chatbot uses one agent for every browser tab, so all chats share the same memory.
