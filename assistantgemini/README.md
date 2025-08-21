# AssistantGemini

A Discord bot cog that provides an AI assistant powered by Google's Gemini language models. This cog allows users to chat with an AI assistant that can remember conversation context and provide intelligent responses.

## Features

- **Gemini AI Integration**: Uses Google's Gemini 2.5 Flash and Pro models
- **Conversation Memory**: Remembers chat history and context
- **Configurable Settings**: Customizable temperature, token limits, and system prompts
- **Function Calling**: Support for custom function registration (Pro models only)
- **Multi-Server Support**: Independent configuration per Discord server
- **Admin Controls**: Comprehensive admin commands for server management
- **Free API Tier**: Utilizes Gemini's generous free tier

## Installation

1. **Install the cog**:
   ```
   [p]cog install assistantgemini
   ```

2. **Get a Gemini API key**:
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Copy the key for use in the bot

3. **Set up the assistant**:
   ```
   [p]assistantgemini setup
   [p]assistantgemini geminikey YOUR_API_KEY_HERE
   ```

## Commands

### User Commands

- `[p]chat <message>` - Chat with the AI assistant
- `[p]clearconvo` - Clear your conversation history
- `[p]convostats` - View your conversation statistics
- `[p]chathelp` - Get tips for better AI interactions

### Admin Commands

- `[p]assistantgemini setup` - Initial setup for the server
- `[p]assistantgemini geminikey <key>` - Set the Gemini API key
- `[p]assistantgemini prompt <prompt>` - Set the system prompt
- `[p]assistantgemini model <model>` - Choose the Gemini model
- `[p]assistantgemini settings` - View current settings

### Advanced Admin Commands

- `[p]assistantgeminiadmin enable/disable` - Enable/disable the assistant
- `[p]assistantgeminiadmin temperature <value>` - Set response creativity (0.0-2.0)
- `[p]assistantgeminiadmin maxtokens <value>` - Set maximum response length
- `[p]assistantgeminiadmin reset` - Reset all settings to defaults
- `[p]assistantgeminiadmin clearallconversations` - Clear all server conversations

## Models

The cog supports the following Gemini models:

- **gemini-1.5-flash** - Fast, efficient responses
- **gemini-1.5-pro** - Advanced reasoning and function calling
- **gemini-2.0-flash** - Latest flash model
- **gemini-2.0-pro** - Latest pro model with advanced capabilities
- **gemini-2.5-flash** - Recommended default (fast + capable)
- **gemini-2.5-pro** - Most advanced model

## Configuration

### System Prompt
Customize how the AI behaves with a system prompt:
```
[p]assistantgemini prompt You are a helpful Discord bot assistant. Be friendly and concise in your responses.
```

### Temperature
Control response creativity:
- **0.0-0.5**: Focused, consistent responses
- **0.5-1.0**: Balanced creativity
- **1.0-2.0**: More creative and varied responses

### Token Limits
- **Max Tokens**: Maximum length of AI responses
- **Max Conversation Tokens**: How much conversation history to remember

## Usage Examples

### Basic Chat
```
User: [p]chat What's the weather like today?
Bot: I don't have access to real-time weather data, but I can help you find weather information or answer other questions!
```

### Mention the Bot
```
User: @BotName Tell me a joke
Bot: Why don't scientists trust atoms? Because they make up everything! 😄
```

### Reply to Bot
```
User: [replies to bot message] Can you explain that further?
Bot: [continues the conversation with context]
```

## Function Calling

For Pro models, you can register custom functions that the AI can call:

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

## Troubleshooting

### Common Issues

1. **"No API key configured"**
   - Run `[p]assistantgemini geminikey YOUR_KEY`

2. **"Assistant not set up"**
   - Run `[p]assistantgemini setup` first

3. **"Model not supported"**
   - Use one of the supported Gemini models listed above

4. **Slow responses**
   - Check your internet connection
   - Consider using a faster model like gemini-2.5-flash

### API Limits

- **Free Tier**: 15 requests per minute
- **Rate Limits**: Respects Gemini's rate limiting
- **Token Counting**: Estimated (Gemini doesn't provide exact counts in free tier)

## Support

For issues or questions:
- Check the bot's error messages
- Review the configuration with `[p]assistantgemini settings`
- Ensure your API key is valid and has sufficient quota

## Credits

- **Author**: Vertyco
- **Original Assistant Cog**: Based on the OpenAI-powered assistant cog
- **Gemini Integration**: Uses Google's Generative AI Python library

## License

This cog is part of the VRT Cogs collection and follows the same licensing terms. 