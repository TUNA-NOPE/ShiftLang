# OpenRouter Model Selection Guide

ShiftLang now supports multiple OpenRouter models for AI-powered translation. You can choose between free models and faster paid options during installation.

## Available Models

### Free Models (No Payment Required)

#### 1. **openrouter/free** (Default)
- **Cost:** Free
- **Speed:** Variable
- **Description:** Auto-router that automatically selects from available free models
- **API Key:** Optional (increases rate limits if provided)
- **Best For:** General use, trying out OpenRouter

#### 2. **google/gemini-2.0-flash-exp:free**
- **Cost:** Free (Experimental)
- **Speed:** Very fast (~2.3 seconds)
- **Context:** 1.05 million tokens
- **API Key:** Optional
- **Best For:** Fast translation, large context needs

#### 3. **meta-llama/llama-3.1-8b-instruct:free**
- **Cost:** Free
- **Speed:** Fast
- **Description:** 8B instruction-tuned model, good for translation
- **API Key:** Optional
- **Best For:** Fast, reliable translation

#### 4. **nvidia/nemotron-3-nano-30b-a3b:free**
- **Cost:** Free
- **Speed:** Fast
- **Parameters:** 30B total, 3.5B active (MoE architecture)
- **Context:** 1 million tokens
- **Languages:** English, German, Spanish, French, Italian, Japanese
- **API Key:** Optional
- **Best For:** Multi-language translation, large context needs, efficient inference

#### 5. **arcee-ai/trinity-mini:free**
- **Cost:** Free
- **Speed:** Fast
- **Parameters:** 26B total, 3B active (128 experts, 8 active per token)
- **Context:** 131k tokens
- **Description:** Designed for multi-turn agents and tool orchestration
- **API Key:** Optional
- **Best For:** Complex conversational translation, structured outputs

### Paid Models (Require Credits)

#### 6. **google/gemini-flash-1.5**
- **Cost:** $0.075/$0.30 per million tokens (input/output)
- **Speed:** Very fast (~2.3 seconds)
- **API Key:** Required (with credits)
- **Best For:** Production use, high-quality translation at low cost

#### 7. **openai/gpt-4o-mini**
- **Cost:** Low (check OpenRouter pricing)
- **Quality:** Excellent translation quality (72.2% accuracy on benchmarks)
- **API Key:** Required (with credits)
- **Best For:** High-quality translation, especially for Japanese/Asian languages

#### 8. **meta-llama/llama-3.3-70b-instruct**
- **Cost:** Moderate (check OpenRouter pricing)
- **Quality:** High quality, efficient
- **API Key:** Required (with credits)
- **Best For:** Complex translation, professional use

## How to Choose a Model

### For Most Users:
- **Start with:** `openrouter/free` (no setup needed)
- **Upgrade to:** `google/gemini-2.0-flash-exp:free` (faster, still free)
- **Multi-language:** `nvidia/nemotron-3-nano-30b-a3b:free` (6 languages, 1M context)
- **Conversational:** `arcee-ai/trinity-mini:free` (multi-turn, structured output)

### For Production/Professional Use:
- **Budget-conscious:** `google/gemini-flash-1.5` ($0.075/$0.30 per M tokens)
- **Best quality:** `openai/gpt-4o-mini` (excellent accuracy)
- **Complex text:** `meta-llama/llama-3.3-70b-instruct` (highest capacity)

## Installation

### During First Install:
```bash
python install.py
```
1. Choose "OpenRouter AI" as your translation provider
2. Select your preferred model from the list
3. For free models, API key is optional
4. For paid models, you'll need to add credits at https://openrouter.ai/keys

### Reconfigure Existing Installation:
```bash
python install.py --reconfigure
```

### Manual Configuration:
Edit `config.json`:
```json
{
  "translation_provider": "openrouter",
  "openrouter_api_key": "your-api-key-here",
  "openrouter_model": "google/gemini-2.0-flash-exp:free"
}
```

## Getting an API Key

1. Visit: https://openrouter.ai/keys
2. Sign up for a free account
3. Create an API key
4. For paid models: Add credits (minimum $5)
5. For free models: No credits needed (key just increases rate limits)

## Testing Your Configuration

Test your OpenRouter setup:
```bash
python test_openrouter.py
```

## Cost Optimization Tips

1. **Use free models for testing** before committing to paid models
2. **Gemini Flash 1.5** offers the best price/performance ratio
3. **Prompt caching** can reduce costs by up to 90% (automatic with Gemini)
4. **Free models** are great for personal use and low-volume translation

## Troubleshooting

### "Authentication failed" error:
- Check your API key in `config.json`
- Ensure you've added credits for paid models
- For free models, try removing the API key

### Translation returns original text:
- Check internet connection
- Verify model name is correct
- Try switching to `openrouter/free`

### Rate limit errors:
- Add an API key to increase limits
- Wait a few minutes between requests
- Consider upgrading to a paid model

## Model Performance Comparison

| Model | Cost | Speed | Quality | Context | Best For |
|-------|------|-------|---------|---------|----------|
| openrouter/free | Free | Medium | Good | Varies | General use |
| gemini-2.0-flash-exp | Free | Fast | Good | 1M+ | Speed + free |
| llama-3.1-8b | Free | Fast | Good | Medium | Fast + reliable |
| nemotron-3-nano | Free | Fast | Good | 1M | Multi-language |
| trinity-mini | Free | Fast | Good | 131k | Multi-turn |
| gemini-flash-1.5 | $0.075 | Very Fast | Great | Large | Production |
| gpt-4o-mini | Low | Fast | Excellent | Large | High quality |
| llama-3.3-70b | Medium | Medium | Excellent | Large | Professional |

## Model Details

### NVIDIA Nemotron 3 Nano 30B A3B
- **Architecture:** Hybrid MoE (Mamba-2 + Transformer)
- **Layers:** 23 Mamba-2/MoE + 6 Attention layers
- **Supported Languages:** English, German, Spanish, French, Italian, Japanese
- **License:** Open weights (check NVIDIA terms)
- **Best Use Cases:** Efficient agentic AI, multi-language translation, large context processing

### Arcee AI Trinity Mini
- **Architecture:** Sparse MoE (128 experts, 8 active per token)
- **Specialization:** Multi-turn agents, tool orchestration, structured outputs
- **License:** Apache 2.0
- **Training:** 10T tokens (Datology partnership)
- **Best Use Cases:** Conversational translation, complex workflows, on-prem deployment

## Sources

- [OpenRouter Models](https://openrouter.ai/models)
- [Free AI Models on OpenRouter](https://openrouter.ai/collections/free-models)
- [OpenRouter Models Ranked (2026)](https://www.teamday.ai/blog/top-ai-models-openrouter-2026)
- [Best Models for Translation](https://skerritt.blog/best-openrouter-models-for-real-time-visual-novel-translation/)
- [NVIDIA Nemotron 3 Nano on OpenRouter](https://openrouter.ai/nvidia/nemotron-3-nano-30b-a3b:free)
- [NVIDIA Nemotron 3 Family](https://huggingface.co/blog/nvidia/nemotron-3-nano-efficient-open-intelligent-models)
- [Arcee AI Trinity Mini on OpenRouter](https://openrouter.ai/arcee-ai/trinity-mini:free)
- [Arcee AI Trinity Documentation](https://www.arcee.ai/trinity)
