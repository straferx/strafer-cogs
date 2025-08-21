# Installation Guide for AssistantGemini

## Prerequisites

- Python 3.10 or higher
- Red-DiscordBot (RedBot) 3.5.0 or higher
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Step 1: Install Dependencies

### Option A: Using pip (Recommended)
```bash
pip install google-generativeai httpx tenacity pydantic
```

### Option B: Using requirements.txt
```bash
pip install -r requirements.txt
```

### Option C: Using setup.py
```bash
python setup.py install
```

## Step 2: Install the Cog

### For RedBot Users
1. Download the `assistantgemini` folder to your RedBot cogs directory
2. Restart your bot
3. Load the cog: `[p]cog load assistantgemini`

### For Manual Installation
1. Copy the `assistantgemini` folder to your bot's cogs directory
2. Ensure all dependencies are installed
3. Restart your bot

## Step 3: Get a Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

## Step 4: Configure the Cog

1. **Setup the assistant:**
   ```
   [p]assistantgemini setup
   ```

2. **Set your API key:**
   ```
   [p]assistantgemini geminikey YOUR_API_KEY_HERE
   ```

3. **Optional: Customize the system prompt:**
   ```
   [p]assistantgemini prompt You are a helpful Discord bot assistant. Be friendly and concise.
   ```

## Step 5: Start Using

- **Chat with the AI:** `[p]chat Hello, how are you?`
- **Mention the bot:** `@BotName Tell me a joke`
- **View settings:** `[p]assistantgemini settings`
- **Get help:** `[p]chathelp`

## Troubleshooting

### Common Issues

1. **"google-generativeai not found"**
   - Run: `pip install google-generativeai`

2. **"httpx not found"**
   - Run: `pip install httpx`

3. **"tenacity not found"**
   - Run: `pip install tenacity`

4. **"pydantic not found"**
   - Run: `pip install pydantic`

### API Key Issues

1. **"No API key configured"**
   - Run: `[p]assistantgemini geminikey YOUR_KEY`

2. **"Invalid API key"**
   - Check your API key at [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Ensure the key is copied correctly

### Bot Issues

1. **"Cog not found"**
   - Ensure the cog is in the correct directory
   - Restart your bot
   - Check bot logs for errors

2. **"Permission denied"**
   - Ensure you have admin permissions in the server
   - Check bot permissions

## Verification

To verify the installation:

1. **Check cog status:**
   ```
   [p]cog list
   ```
   You should see `assistantgemini` in the list.

2. **Test basic functionality:**
   ```
   [p]assistantgemini settings
   ```
   This should show the current settings.

3. **Test chat:**
   ```
   [p]chat Hello, test message
   ```
   The bot should respond with an AI-generated message.

## Support

If you encounter issues:

1. Check the bot logs for error messages
2. Verify all dependencies are installed
3. Ensure your API key is valid
4. Check that you have the required permissions

## Next Steps

After successful installation:

1. **Install AssistantGemini Utils (Optional):**
   - Copy the `assistantgeminiutils` folder to your cogs directory
   - Load it: `[p]cog load assistantgeminiutils`

2. **Customize settings:**
   - Adjust temperature: `[p]assistantgeminiadmin temperature 0.8`
   - Set max tokens: `[p]assistantgeminiadmin maxtokens 1500`
   - Change model: `[p]assistantgemini model gemini-2.5-pro`

3. **Explore advanced features:**
   - Function calling (Pro models only)
   - Conversation management
   - Admin controls 