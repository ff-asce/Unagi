# Google Gemini Setup Guide for UNAGI

## Quick Setup

1. **Get your API key** from: https://aistudio.google.com/app/apikey

2. **Create `.env` file** in the project root with:
   ```bash
   LLM_API_KEY=your_actual_api_key_here
   LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   LLM_MODEL_NAME=gemini-1.5-flash
   ```

3. **Replace** `your_actual_api_key_here` with the key you copied

## Model Options

Choose one for `LLM_MODEL_NAME`:

- **`gemini-1.5-flash`** (Recommended)
  - Faster responses
  - Lower cost
  - Great for nutrition tracking

- **`gemini-1.5-pro`**
  - More capable
  - Better reasoning
  - Higher cost

## How This Works

Google Gemini now supports OpenAI-compatible API calls. This means:
- UNAGI uses the `openai` Python library
- But connects to Google's servers instead
- Your API key authenticates with Google
- The base URL routes requests to Gemini

## Official Documentation

- **OpenAI Compatibility**: https://ai.google.dev/gemini-api/docs/openai
- **Available Models**: https://ai.google.dev/gemini-api/docs/models/gemini
- **API Reference**: https://ai.google.dev/api

## Troubleshooting

**Error: "Invalid API key"**
- Double-check you copied the full key from Google AI Studio
- Make sure there are no extra spaces or quotes

**Error: "Model not found"**
- Use exactly: `gemini-1.5-flash` or `gemini-1.5-pro`
- Model names are case-sensitive

**Error: "Rate limit exceeded"**
- Free tier has limits (15 requests/minute for Flash, 2/minute for Pro)
- Wait a minute and try again
- Consider upgrading to paid tier if needed

## Alternative: Use Other LLMs

UNAGI supports any OpenAI-compatible API. You can also use:

### OpenAI (ChatGPT)
```bash
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
```

### Anthropic Claude (via OpenRouter)
```bash
LLM_API_KEY=sk-or-...
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL_NAME=anthropic/claude-3.5-sonnet
```

### Groq (Fast inference)
```bash
LLM_API_KEY=gsk_...
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL_NAME=llama-3.1-70b-versatile
```

### Local Ollama
```bash
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=llama3.1