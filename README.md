Discord AI Conversation Automator
A Python-based automation framework designed to simulate natural human-like interactions between multiple accounts on Discord using Large Language Models (DeepSeek API). The project focuses on "reviving" community servers by generating context-aware conversations.

🚀 Key Features
Human-Like Simulation: Implements character-by-character typing with randomized delays and natural pauses.
Context-Aware Responses: Extracts recent chat history (DOM scraping) to provide relevant AI-generated replies.
Advanced Scheduling: * Dynamic daily schedules (different hours for Mon-Sun).
Randomized message frequency (min/max messages per day).
Automatic generation of random timestamps to avoid detection.
Multi-Account & Multi-Channel Support: Manage different characters and channels through a single config.json.
Robust Logging: Dual-handler logging (Console + Rotating File) for long-term monitoring and debugging.
Headless Execution: Fully compatible with Linux/Debian environments (VDS/VPS) using Chrome Headless mode.

🛠 Tech Stack
Core: Python 3.x
Automation: Selenium WebDriver (Chrome)
AI Integration: DeepSeek API (REST)
Data Management: JSON-based configuration & buffering
Logging: Python logging with RotatingFileHandler

📁 Project Structure
main.py: The orchestrator. Handles scheduling, task queuing, and global state management.
browser.py: Selenium-based module for Discord interaction, message parsing, and typing simulation.
ai.py: DeepSeek API wrapper for generating persona-based responses.
config.json: Main configuration file for channels, schedules, and user tokens.
Bufer_config.json: Persistence layer for daily timestamps and task tracking.
