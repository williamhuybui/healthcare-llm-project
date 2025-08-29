# Healthcare LLM Project

A FastAPI-based web application with LangGraph conversational AI agents featuring multiple tools and capabilities.

## 🚀 Features

### FastAPI Web Server
- Simple REST API with JSON responses
- Auto-reload development server
- Production-ready with uvicorn

### LangGraph AI Agents
- **Level 1**: Basic conversational agent with memory
- **Level 2**: Advanced agent with multiple tools:
  - 🧮 **Calculator** - Mathematical expressions and functions
  - 🔍 **Web Search** - Real-time search via Tavily API
  - 🕐 **Time Service** - Current date and time
  - 🌐 **IP Lookup** - Public IP address detection
  - 📍 **Geolocation** - City location by IP address
- **Level 3**: ReAct (Reasoning + Acting) agent with enhanced instructions:
  - 🤖 **GPT-4o Model** - Latest OpenAI model with improved reasoning
  - 🎯 **Task Decomposition** - Breaks complex tasks into logical steps
  - 🌍 **Multilingual Greetings** - Responds "Xin Chao" to Vietnamese users
  - 🔒 **Privacy-Focused** - Doesn't reveal internal tool capabilities

## 📁 Project Structure

```
healthcare-llm-project/
├── main.py                    # FastAPI web server
├── langchain_template/
│   ├── lv1_conversational.py     # Basic conversational agent
│   ├── lv2_conversational_w_tools.py # Advanced agent with tools
│   ├── lv3_ReAct_w_instruction.py # ReAct agent with enhanced instructions
│   └── main.py                    # Original agent template
├── requirements.txt           # Python dependencies
├── setup_env.ps1             # Windows environment setup
├── .env                      # Environment variables
├── .gitignore               # Git ignore rules
└── AZURE_DEPLOYMENT.md      # Azure deployment guide
```

## 🛠 Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- Tavily API key (for search functionality)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/williamhuybui/healthcare-llm-project
   cd healthcare-llm-project
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Or use the setup script
   .\setup_env.ps1
   
   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create/update `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

## 🚀 Usage

### FastAPI Server
```bash
# Development server
python main.py

# Or with uvicorn
uvicorn main:app --reload
```
Access at: http://127.0.0.1:8000

### Conversational Agents

#### Basic Agent (Level 1)
```bash
cd langchain_template
python lv1_conversational.py
```

#### Advanced Agent with Tools (Level 2)
```bash
cd langchain_template
python lv2_conversational_w_tools.py
```

#### ReAct Agent with Enhanced Instructions (Level 3)
```bash
cd langchain_template
python lv3_ReAct_w_instruction.py
```

#### Example Interactions

**Level 2 Agent:**
```
🧑 You: What's 25 * 4 + sqrt(144)?
🔧 Tool: calculator("25 * 4 + sqrt(144)")
🤖 AI: The result is 112

🧑 You: What time is it?
🔧 Tool: get_time()
🤖 AI: The current time is 2024-01-15 14:30:25

🧑 You: Where am I located?
🔧 Tool: get_public_ip()
🔧 Tool: get_city_by_ip()
🤖 AI: You appear to be located in San Francisco, US
```

**Level 3 ReAct Agent:**
```
🧑 You: Hi there!
🤖 AI: Xin Chao! How can I help you today?

🧑 You: I need to plan a trip to Vietnam and calculate the budget
🤖 AI: I'd be happy to help you plan your trip to Vietnam and calculate your budget. Let me break this down into steps:

1. First, let me search for current travel information about Vietnam...
2. Then I'll help you calculate costs for different aspects of your trip...

[Agent proceeds with step-by-step assistance]
```

## 🔧 Available Tools

| Tool | Function | Example Usage |
|------|----------|---------------|
| Calculator | Mathematical expressions | `2+2`, `sqrt(16)`, `5!`, `sin(pi/2)` |
| Web Search | Real-time search results | `"latest news about AI"` |
| Time Service | Current date/time | `"what time is it?"` |
| IP Lookup | Public IP address | `"what's my IP?"` |
| Geolocation | Location by IP | `"where am I?"` |

## 🌐 Deployment

### Azure App Service
See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for detailed Azure deployment instructions.

### Local Production
```bash
# Using gunicorn (Linux/Mac)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using uvicorn (Windows/Cross-platform)
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📝 API Documentation

Once running, visit:
- **Interactive docs**: http://127.0.0.1:8000/docs
- **Alternative docs**: http://127.0.0.1:8000/redoc

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API authentication | Yes |
| `TAVILY_API_KEY` | Tavily search API key | Yes |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**ModuleNotFoundError**: Ensure virtual environment is activated and dependencies are installed
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

**API Key Errors**: Verify your API keys are correctly set in the `.env` file

**Port Already in Use**: Change the port in `main.py` or kill the existing process

### Getting Help
- Check the error logs in the console
- Verify environment variables are loaded
- Ensure all dependencies are installed

### Up-to-speed

https://learngitbranching.js.org/