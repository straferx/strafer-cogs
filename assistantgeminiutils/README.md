# AssistantGemini Utils

A utility cog that extends the AssistantGemini cog with pre-built functions that the AI can call. This cog automatically registers useful functions with the main assistant, allowing users to access real-time information and perform actions through natural language.

## Features

- **Automatic Function Registration**: Functions are automatically registered when the cog loads
- **Real-time Information**: Access to current time, member balances, and internet search
- **Seamless Integration**: Works automatically with the AssistantGemini cog
- **No Commands**: This cog operates silently in the background

## Installation

1. **Install the cog**:
   ```
   [p]cog install assistantgeminiutils
   ```

2. **Ensure AssistantGemini is installed**: This cog requires the main AssistantGemini cog to function

## Available Functions

### Get Current Time
- **Function**: `get_current_time`
- **Description**: Get the current date and time
- **Parameters**: 
  - `timezone` (optional): Timezone to get time for
  - Supported timezones: UTC, America/New_York, Europe/London, Asia/Tokyo

**Example Usage**:
```
User: What time is it in New York?
AI: Let me check the current time in New York for you.
[AI calls get_current_time with timezone="America/New_York"]
```

### Get Member Balance
- **Function**: `get_member_balance`
- **Description**: Get a Discord member's balance from the economy cog
- **Parameters**:
  - `member_id`: Discord user ID to get balance for

**Example Usage**:
```
User: What's my balance?
AI: I'll check your current balance.
[AI calls get_member_balance with the user's ID]
```

### Search Internet
- **Function**: `search_internet`
- **Description**: Search the internet for current information
- **Parameters**:
  - `query`: Search query to look up
  - `max_results` (optional): Maximum number of results (1-5, default: 3)

**Example Usage**:
```
User: What's the latest news about AI?
AI: Let me search for the latest AI news for you.
[AI calls search_internet with query="latest AI news"]
```

## How It Works

1. **Automatic Registration**: When the cog loads, it automatically registers all utility functions with the AssistantGemini cog
2. **Function Calling**: When users ask questions that require real-time data, the AI can call these functions
3. **Seamless Experience**: Users don't need to know about the underlying functions - they just ask questions naturally

## Requirements

- **AssistantGemini Cog**: Must be installed and configured
- **Python Dependencies**: 
  - `duckduckgo_search` - For internet search functionality
  - `pytz` - For timezone handling

## Configuration

This cog requires no configuration. It automatically:
- Detects the AssistantGemini cog
- Registers all available functions
- Handles function registration/unregistration on cog load/unload

## Troubleshooting

### Common Issues

1. **"Functions not registered"**
   - Ensure AssistantGemini cog is installed and loaded
   - Check bot logs for registration errors

2. **"Function not found"**
   - Restart the bot to reload the cog
   - Check that both cogs are properly installed

3. **Search not working**
   - Ensure `duckduckgo_search` is installed
   - Check internet connectivity

### Log Messages

The cog provides helpful log messages:
- `Successfully registered utility functions with AssistantGemini`
- `Successfully unregistered utility functions from AssistantGemini`
- `AssistantGemini cog not found. Functions will not be registered.`

## Development

### Adding New Functions

To add new utility functions:

1. **Define the function schema** in `_register_utility_functions()`
2. **Add the function name** to `_get_function_names()`
3. **Implement the actual function logic** in the AssistantGemini cog

### Function Schema Format

```python
function_schema = {
    "name": "function_name",
    "description": "What the function does",
    "parameters": {
        "type": "object",
        "properties": {
            "param_name": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param_name"]
    }
}
```

## Credits

- **Author**: Vertyco
- **Purpose**: Extends AssistantGemini with utility functions
- **Integration**: Seamlessly works with the main assistant cog

## License

This cog is part of the VRT Cogs collection and follows the same licensing terms. 