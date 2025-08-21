# Example Functions for AssistantGemini

This directory contains example functions that demonstrate how to create custom functions for the AssistantGemini cog. These functions can be called by the AI assistant to provide additional functionality beyond basic chat.

## Available Examples

### get_date.py
- **Purpose**: Get current date and time for different timezones
- **Function**: `get_current_time(timezone)`
- **Parameters**: 
  - `timezone` (optional): Timezone string (e.g., "UTC", "America/New_York")
- **Returns**: Formatted date and time string

### get_member_balance.py
- **Purpose**: Get a Discord member's balance from economy cogs
- **Function**: `get_member_balance(member_id)`
- **Parameters**:
  - `member_id`: Discord user ID
- **Returns**: Member's current balance

### search_internet.py
- **Purpose**: Search the internet for current information
- **Function**: `search_internet(query, max_results)`
- **Parameters**:
  - `query`: Search query string
  - `max_results` (optional): Maximum number of results (default: 3)
- **Returns**: Search results as formatted text

## How to Use These Examples

1. **Copy the function code** into your own cog
2. **Register the function** with AssistantGemini using the schema
3. **Implement the actual logic** for your specific use case

## Function Registration

To register a function with AssistantGemini:

```python
# In your cog's cog_load method
async def cog_load(self):
    assistant_cog = self.bot.get_cog("AssistantGemini")
    if assistant_cog:
        assistant_cog.register_function(
            "yourcog",
            "function_name",
            FUNCTION_SCHEMA,
            "user"  # permission level
        )
```

## Schema Format

Each function should include a `FUNCTION_SCHEMA` that defines:

- **name**: Function identifier
- **description**: What the function does
- **parameters**: Input parameters and their types
- **required**: List of required parameters

## Best Practices

1. **Error Handling**: Always include proper error handling
2. **Async Functions**: Use async functions for better performance
3. **Clear Descriptions**: Provide clear descriptions for the AI to understand
4. **Parameter Validation**: Validate input parameters
5. **Return Values**: Return meaningful, formatted results

## Testing

You can test these functions independently:

```bash
python get_date.py
python get_member_balance.py
python search_internet.py
```

## Dependencies

These examples require:
- `pytz` - For timezone handling
- `duckduckgo_search` - For internet search
- Discord.py - For Discord bot functionality

## Contributing

Feel free to add more example functions or improve existing ones. Make sure to:
- Include proper documentation
- Add error handling
- Provide a clear function schema
- Test the function thoroughly 