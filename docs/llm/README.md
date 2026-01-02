# LLM Provider Operations Guide

## Model Management

### List Models
```bash
docker exec -it ollama ollama list
```

### Update Models
```bash
docker exec -it ollama ollama pull llama3
docker exec -it ollama ollama pull nomic-embed-text
```

### Remove Models
```bash
docker exec -it ollama ollama rm llama3
docker exec -it ollama ollama rm nomic-embed-text
```

## Performance Tuning

### Ollama Memory Settings
Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Increase for larger models
```

### LLM Parameters
- `max_tokens`: Limit response length (default: 1000)
- `temperature`: Control randomness (0-1, default: 0.7)

## Troubleshooting

### "Connection refused" Error
1. Check Ollama container: `docker ps | grep ollama`
2. Check logs: `docker logs ollama`
3. Verify port: `curl http://localhost:11434/api/version`

### Slow Response
1. Check model size (llama3: ~4.7GB)
2. Monitor memory: `docker stats ollama`
3. Consider smaller model (llama3:8b vs llama3:70b)

### Embedding Dimension Mismatch
- Ensure nomic-embed-text is used (768 dimensions)
- OpenAI alternative: text-embedding-3-small with `dimensions=768`

## Switching Between Providers

### From Ollama to OpenAI

1. Update `.env`:
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your-api-key-here
   ```

2. Restart application

### From OpenAI to Ollama

1. Update `.env`:
   ```bash
   LLM_PROVIDER=ollama
   ```

2. Ensure Ollama container is running:
   ```bash
   docker-compose up -d ollama
   ```

3. Restart application

## Testing

### Integration Test
```bash
cd backend
source venv/bin/activate
python scripts/test_ollama_integration.py
```

### Unit Tests
```bash
cd backend
source venv/bin/activate
pytest tests/test_ollama.py -v
```

### Manual Testing

Test LLM generation:
```bash
cd backend
source venv/bin/activate
python -c "
import asyncio
from app.llm.provider_factory import LLMProviderFactory

async def test():
    provider = LLMProviderFactory.get_provider()
    response = await provider.generate('Hello, who are you?', max_tokens=100)
    print(response)

asyncio.run(test())
"
```

Test embeddings:
```bash
cd backend
source venv/bin/activate
python -c "
import asyncio
from app.llm.provider_factory import LLMProviderFactory

async def test():
    provider = LLMProviderFactory.get_provider()
    vector = await provider.embed('Test text')
    print(f'Dimension: {len(vector)}')
    print(f'First 5 values: {vector[:5]}')

asyncio.run(test())
"
```
