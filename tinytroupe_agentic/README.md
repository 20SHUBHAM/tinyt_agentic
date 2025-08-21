# Agentic Focus Group System

A complete end-to-end automation system for TinyTroupe focus group discussions with intelligent agents.

## 🚀 Features

### Core Capabilities
- **Automated Persona Generation**: AI-powered creation of diverse, realistic TinyPersons based on context prompts
- **Intelligent Discussion Moderation**: Automated focus group discussions with natural conversation flow
- **Real-time Summary Generation**: Structured summaries following predefined schemas
- **Interactive Q&A System**: Ask questions about discussion insights and get AI-powered answers
- **Persistent Session Management**: Complete memory of discussions and participants

### Agentic Architecture
- **PersonaGeneratorAgent**: Creates diverse personas with realistic backgrounds and budgets
- **DiscussionModeratorAgent**: Conducts natural focus group discussions with group dynamics
- **SummaryGeneratorAgent**: Generates comprehensive structured summaries automatically
- **QAAssistantAgent**: Provides interactive Q&A capabilities over discussion data

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla), Bootstrap 5
- **AI Integration**: OpenAI API compatible (optional)
- **Storage**: JSON-based session management
- **Deployment**: Docker, Replit ready

## 📋 Prerequisites

- Python 3.11 or higher
- pip or conda for package management
- (Optional) OpenAI API key for enhanced AI responses

## 🚀 Quick Start

### Option 1: Replit Deployment (Recommended)

1. **Fork/Import to Replit**:
   - Go to [Replit](https://replit.com)
   - Create a new Repl from GitHub
   - Import this repository

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings (OpenAI key is optional)
   ```

3. **Run**:
   - Click the "Run" button in Replit
   - The application will be available at your Repl URL

### Option 2: Local Development

1. **Clone Repository**:
   ```bash
   git clone <repository-url>
   cd agentic-focus-group
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run Application**:
   ```bash
   python main.py
   ```

5. **Access Application**:
   - Open http://localhost:8000 in your browser

### Option 3: Docker Deployment

1. **Build Image**:
   ```bash
   docker build -t agentic-focus-group .
   ```

2. **Run Container**:
   ```bash
   docker run -p 8000:8000 agentic-focus-group
   ```

## 📖 How to Use

### Step 0: Generate and Edit Discussion Plan
1. Enter a brief topic description in the Plan section
2. Click "Generate Plan" to get an LLM-crafted framework (phases, goals, prompts)
3. Edit the generated plan text if needed
4. Click "Accept Plan & Continue" to proceed

### Step 1: Generate TinyPersons
1. Enter a **Context Prompt** describing your target audience:
   ```
   I want to create a diverse group of Gen Z consumers aged 18-25 from urban India 
   who are active on social media and interested in beauty/cosmetics. Include different 
   personality types like enthusiastic early adopters, budget-conscious researchers, 
   and trend-following influencer watchers.
   ```

2. Enter your **Discussion Topic**:
   ```
   Online beauty shopping experiences and preferences
   ```

3. Click **"Generate Personas"**

### Step 2: Review & Edit
- Review the generated personas with their backgrounds, budgets, and personality types
- Edit any persona backgrounds if needed
- Modify the discussion topic if required
- Click **"Update Personas & Topic"** if changes were made
- Click **"Start Discussion"** when ready

### Step 3: Automated Discussion
- The system automatically conducts a multi-phase focus group discussion
- Watch the progress as AI agents moderate the conversation
- Discussion includes natural interruptions, agreements, and group dynamics

### Step 4: Results & Q&A
- **Summary Tab**: View the structured summary with themes, insights, and recommendations
- **Transcript Tab**: Read the complete discussion transcript
- **Q&A Tab**: Ask questions about the discussion and get intelligent answers

## 🤖 Agent System

### PersonaGeneratorAgent
- Analyzes context prompts to understand requirements
- Generates diverse personas with realistic demographics
- Creates detailed backgrounds with authentic Indian contexts
- Ensures personality and income diversity

### DiscussionModeratorAgent
- Conducts structured focus group discussions
- Manages natural conversation flow and transitions
- Creates spontaneous interactions and group dynamics
- Handles different discussion phases (opening, exploration, deep-dive, etc.)

### SummaryGeneratorAgent
- Generates comprehensive summaries following predefined schemas
- Analyzes themes, sentiment, and behavioral patterns
- Provides actionable business insights and recommendations
- Extracts key quotes and verbatim highlights

### QAAssistantAgent
- Answers questions about discussion content intelligently
- Categorizes questions and provides contextual responses
- Suggests follow-up questions based on conversation
- Maintains conversation history for context

## 📊 Summary Schema

The system generates structured summaries with the following sections:

- **Executive Summary**: Overview, main themes, key insights
- **Participant Analysis**: Demographics, engagement patterns, speaking behavior
- **Thematic Analysis**: Primary themes, consensus areas, divergent opinions
- **Behavioral Insights**: Purchase drivers, barriers, decision processes
- **Sentiment Analysis**: Overall sentiment, emotional triggers
- **Actionable Insights**: Opportunities, recommendations, risk areas
- **Verbatim Highlights**: Representative quotes, contrasting viewpoints

## 🔧 Configuration

### Environment Variables

```bash
# LLM (optional, enables dynamic, non-hardcoded agent behavior)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_RETRIES=3

# App
DEBUG=True
```

### TinyTroupe Integration

- This app includes an adapter that uses the real TinyTroupe if available.
- The PyPI package is a placeholder; install from GitHub per their README.
- When TinyTroupe is present, `TinyPerson`, `TinyWorld`, and `control` are delegated automatically.

### Customization Options

- **Persona Templates**: Modify `agents/persona_generator.py` to customize persona generation
- **Discussion Flow**: Edit `agents/discussion_moderator.py` to change discussion structure
- **Summary Schema**: Update `agents/summary_generator.py` to modify summary format
- **UI Styling**: Customize `static/css/style.css` for visual changes

## 🔍 API Endpoints

- `GET /` - Main application interface
- `POST /generate-personas` - Generate personas from context
- `POST /generate-plan` - Generate LLM discussion plan from topic brief
- `POST /accept-plan` - Accept edited plan and attach to session
- `POST /update-personas` - Update personas and topic
- `POST /start-discussion/{session_id}` - Start automated discussion
- `GET /session-status/{session_id}` - Get discussion status
- `GET /discussion-results/{session_id}` - Get results and summary
- `POST /ask-question` - Interactive Q&A system
- `GET /health` - Health check endpoint

## 🎯 Use Cases

### Market Research
- Consumer behavior studies
- Product feedback sessions
- Brand perception research
- User experience research

### Product Development
- Feature validation
- User needs assessment
- Competitive analysis
- Innovation ideation

### Marketing Strategy
- Campaign message testing
- Target audience insights
- Channel preference analysis
- Influencer impact studies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
1. Check the existing issues
2. Create a new issue with detailed description
3. Include steps to reproduce any bugs
4. Provide system information and logs

## 🔮 Future Enhancements

- Integration with real TinyTroupe library
- Multi-language support
- Video/audio discussion simulation
- Advanced analytics dashboard
- Export capabilities (PDF, Excel, etc.)
- Integration with business intelligence tools
- Real-time collaboration features

---

**Built with ❤️ using AI-powered automation for better market research**