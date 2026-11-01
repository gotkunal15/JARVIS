
# JARVIS

Your personal AI assistant.

## Features

- AI chat using OmniRoute
- Persistent conversation history
- Automatic memory saving
- Voice input and output
- Wake-word detection
- Basic Windows computer control
- Flask-powered web interface

## Requirements

- Windows 10 or later
- Python 3.14
- Git
- OmniRoute
- Microsoft Edge recommended for voice features

## Installation

Clone the repository:

```bash
git clone https://github.com/gotkunal15/JARVIS.git
cd JARVIS
```

Create a virtual environment:

```bash
py -m venv jarvis-env
jarvis-env\Scripts\activate
```

Install dependencies:

```bash
py -m pip install flask requests
```

## Configuration

Make sure OmniRoute is running.

JARVIS currently uses:

- API endpoint: `http://127.0.0.1:20128/v1/chat/completions`
- Model: `kiro/claude-sonnet-4.5`

## Run JARVIS

```bash
py app.py
```

Open:

http://127.0.0.1:8765

## Security

Never upload API keys, passwords, or personal memory databases.

## Author

Kunal Dave

## Project

[GitHub Repository](https://github.com/gotkunal15/JARVIS)
