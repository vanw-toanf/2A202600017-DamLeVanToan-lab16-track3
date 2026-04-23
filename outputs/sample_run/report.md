# Lab 16 Benchmark Report

## Metadata
- Dataset: hotpot_100.json
- Mode: real
- Records: 200
- Agents: react, reflexion

## Summary
| Metric | ReAct | Reflexion | Delta |
|---|---:|---:|---:|
| EM | 0.83 | 0.99 | 0.16 |
| Avg attempts | 1 | 1.19 | 0.19 |
| Avg token estimate | 466.38 | 649.51 | 183.13 |
| Avg latency (ms) | 3072.21 | 4274.08 | 1201.87 |

## Cost Estimation (API Usage)
- **Total Tokens Consumed:** 111,589 tokens
- **Local (Colab / Ollama):** $0.00 (Free)
- **GPT-4o-mini / Gemini 1.5 Flash (~$0.15 / 1M):** ~$0.0167
- **GPT-4o / Claude 3.5 Sonnet (~$10.00 / 1M):** ~$1.1159

## Failure modes
```json
{
  "react": {
    "none": 83,
    "wrong_final_answer": 17
  },
  "reflexion": {
    "none": 99,
    "wrong_final_answer": 1
  }
}
```

## Extensions implemented
- structured_evaluator
- reflection_memory
- benchmark_report_json

## Discussion
Reflexion helps when the first attempt stops after the first hop or drifts to a wrong second-hop entity, guided by reflection memory. The tradeoff is higher attempts, token cost from multiple LLM calls, and increased latency. The local endpoint handled formatting fine, indicating that small LLMs can be utilized for reflection.
