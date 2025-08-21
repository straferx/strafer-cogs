# Strafer Cogs - AssistantGemini

This repository contains Discord bot cogs, including the newly created **AssistantGemini** cog that provides AI assistant functionality using Google's Gemini API instead of OpenAI's ChatGPT.

## What's New

### AssistantGemini Cog
A complete rewrite of the original assistant cog to use Google's Gemini API:

- **Free API Tier**: Utilizes Gemini's generous free tier (15 requests/minute)
- **Modern Models**: Supports Gemini 1.5, 2.0, and 2.5 models
- **Function Calling**: Advanced function calling capabilities with Pro models
- **Conversation Memory**: Maintains chat context and history
- **Multi-Server Support**: Independent configuration per Discord server

### AssistantGemini Utils Cog
A utility cog that extends AssistantGemini with pre-built functions:

- **Automatic Registration**: Functions are automatically registered when loaded
- **Real-time Information**: Access to current time, member balances, internet search
- **Seamless Integration**: Works automatically with the main assistant cog

## Key Changes from Original Assistant Cog

| Feature | Original (OpenAI) | New (Gemini) |
|---------|-------------------|--------------|
| **API Provider** | OpenAI ChatGPT | Google Gemini |
| **Cost** | Pay-per-token | Free tier (15 req/min) |
| **Models** | GPT-3.5, GPT-4 | Gemini 1.5/2.0/2.5 |
| **Token Limits** | 4K-128K tokens | 1M tokens per model |
| **Function Calling** | OpenAI Functions | Gemini Tools |
| **Embeddings** | OpenAI Embeddings | Hash-based (placeholder) |

## Installation

### 1. Install the Main Cog
```bash
[p]cog install assistantgemini
```

### 2. Install the Utils Cog (Optional)
```bash
[p]cog install assistantgeminiutils
```

### 3. Get a Gemini API Key
- Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
- Create a new API key
- Copy the key for use in the bot

### 4. Set Up the Assistant
```
[p]assistantgemini setup
[p]assistantgemini geminikey YOUR_API_KEY_HERE
```

## Quick Start

1. **Setup**: `[p]assistantgemini setup`
2. **Configure API Key**: `[p]assistantgemini geminikey YOUR_KEY`
3. **Start Chatting**: `[p]chat Hello, how are you?`
4. **Mention Bot**: `@BotName Tell me a joke`

## Commands

### User Commands
- `[p]chat <message>` - Chat with the AI
- `[p]clearconvo` - Clear conversation history
- `[p]convostats` - View conversation statistics
- `[p]chathelp` - Get chat tips

### Admin Commands
- `[p]assistantgemini setup` - Initial setup
- `[p]assistantgemini geminikey <key>` - Set API key
- `[p]assistantgemini prompt <prompt>` - Set system prompt
- `[p]assistantgemini model <model>` - Choose AI model
- `[p]assistantgemini settings` - View current settings

### Advanced Admin Commands
- `[p]assistantgeminiadmin enable/disable` - Enable/disable assistant
- `[p]assistantgeminiadmin temperature <value>` - Set creativity (0.0-2.0)
- `[p]assistantgeminiadmin maxtokens <value>` - Set response length
- `[p]assistantgeminiadmin reset` - Reset to defaults

## Supported Models

| Model | Type | Features | Use Case |
|-------|------|----------|----------|
| **gemini-1.5-flash** | Fast | Basic chat, vision | Quick responses |
| **gemini-1.5-pro** | Pro | Function calling, reasoning | Advanced tasks |
| **gemini-2.0-flash** | Fast | Latest flash model | Balanced performance |
| **gemini-2.0-pro** | Pro | Latest pro model | Maximum capability |
| **gemini-2.5-flash** | Fast | **Recommended default** | Best balance |
| **gemini-2.5-pro** | Pro | Most advanced | Complex reasoning |

## Configuration Examples

### System Prompt
```
[p]assistantgemini prompt You are a helpful Discord bot assistant. Be friendly, concise, and helpful. Always provide accurate information and admit when you're unsure about something.
```

### Temperature Settings
```
[p]assistantgeminiadmin temperature 0.3  # More focused, consistent
[p]assistantgeminiadmin temperature 0.7  # Balanced (default)
[p]assistantgeminiadmin temperature 1.2  # More creative, varied
```

### Token Limits
```
[p]assistantgeminiadmin maxtokens 500      # Shorter responses
[p]assistantgeminiadmin maxtokens 2000     # Longer responses
[p]assistantgeminiadmin maxconvotokens 8000 # More conversation history
```

## Function Calling

For Pro models, you can register custom functions:

```python
# Example function registration
function_schema = {
    "name": "get_weather",
    "description": "Get current weather for a location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"]
    }
}

# Register with the assistant
self.bot.get_cog("AssistantGemini").register_function(
    "mycog", "get_weather", function_schema
)
```

## Benefits of Gemini Over OpenAI

### Cost
- **OpenAI**: Pay per token (can be expensive for high usage)
- **Gemini**: Free tier with 15 requests/minute, then pay-per-token

### Model Capabilities
- **OpenAI**: GPT-3.5 (4K tokens), GPT-4 (8K-128K tokens)
- **Gemini**: All models support 1M tokens, better reasoning

### API Reliability
- **OpenAI**: Sometimes rate limited, API outages
- **Gemini**: Generally more stable, better uptime

### Function Calling
- **OpenAI**: Functions API (deprecated), Tools API
- **Gemini**: Modern Tools API with better integration

## Troubleshooting

### Common Issues

1. **"No API key configured"**
   - Run `[p]assistantgemini geminikey YOUR_KEY`

2. **"Assistant not set up"**
   - Run `[p]assistantgemini setup` first

3. **"Model not supported"**
   - Use one of the supported Gemini models listed above

4. **Slow responses**
   - Check internet connection
   - Use faster models like gemini-2.5-flash

### API Limits
- **Free Tier**: 15 requests per minute
- **Rate Limits**: Respects Gemini's rate limiting
- **Token Counting**: Estimated (Gemini doesn't provide exact counts in free tier)

## Development

### Project Structure
```
assistantgemini/
├── __init__.py              # Cog initialization
├── assistantgemini.py       # Main cog class
├── abc.py                   # Abstract base classes
├── commands/                # Command implementations
│   ├── base.py             # User commands
│   └── admin.py            # Admin commands
├── common/                  # Core functionality
│   ├── api.py              # Gemini API integration
│   ├── calls.py            # API call functions
│   ├── chat.py             # Chat handling
│   ├── constants.py        # Constants and models
│   ├── functions.py        # Function registry
│   ├── models.py           # Data models
│   └── utils.py            # Utility functions
├── example-funcs/           # Example functions
├── listener.py              # Message listener
├── locales/                 # Internationalization
└── README.md               # Documentation

assistantgeminiutils/
├── __init__.py              # Cog initialization
├── main.py                  # Main utility cog
├── abc.py                   # Abstract base classes
└── README.md               # Documentation
```

### Adding New Functions
1. Create function in `example-funcs/`
2. Define function schema
3. Register with AssistantGemini cog
4. Test thoroughly

## Credits

- **Original Author**: Vertyco
- **Gemini Integration**: Complete rewrite for Google's Gemini API
- **Purpose**: Provide free AI assistant functionality for Discord bots

## License

This project follows the same licensing terms as the original VRT Cogs collection.

## Support

For issues or questions:
- Check the bot's error messages
- Review configuration with `[p]assistantgemini settings`
- Ensure API key is valid and has sufficient quota
- Check bot logs for detailed error information

---

**Note**: This cog is a complete rewrite of the original assistant cog, designed to work with Google's Gemini API instead of OpenAI. It maintains the same user experience while providing access to Gemini's powerful language models and free tier. 
