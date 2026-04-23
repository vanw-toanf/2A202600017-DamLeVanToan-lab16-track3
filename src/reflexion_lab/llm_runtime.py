import time
import json
import re
from openai import OpenAI
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
import os
from dotenv import load_dotenv

load_dotenv()

llm_link = os.getenv("LLM_LINK")
client = OpenAI(
    base_url=llm_link,
    api_key="ollama",
)

def parse_json_from_text(text: str) -> dict:
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback trying to find the first `{` and last `}`
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        return {}

def call_llm(system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        latency_ms = int((time.time() - start_time) * 1000)
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return content, tokens, latency_ms
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return str(e), 0, latency_ms

def actor_answer_real(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> tuple[str, int, int]:
    context_str = "\n".join([f"Title: {c.title}\nText: {c.text}" for c in example.context])
    user_prompt = f"Context:\n{context_str}\n\nQuestion: {example.question}\n"
    
    if reflection_memory:
        mem_str = "\n".join([f"- {m}" for m in reflection_memory])
        user_prompt += f"\nPrevious lessons and strategies:\n{mem_str}\n"
    
    user_prompt += "\nPlease provide only the final answer."
    
    content, tokens, latency = call_llm(ACTOR_SYSTEM, user_prompt)
    return content.strip(), tokens, latency

def evaluator_real(example: QAExample, answer: str) -> tuple[JudgeResult, int, int]:
    user_prompt = f"Question: {example.question}\nGold Answer: {example.gold_answer}\nPredicted Answer: {answer}"
    content, tokens, latency = call_llm(EVALUATOR_SYSTEM, user_prompt)
    
    parsed = parse_json_from_text(content)
    score = parsed.get("score", 0)
    reason = parsed.get("reason", "Failed to parse Evaluator JSON.")
    
    if "score" not in parsed:
        if '"score": 1' in content or '"score":1' in content:
            score = 1
        elif '"score": 0' in content or '"score":0' in content:
            score = 0
            
    return JudgeResult(score=score, reason=reason), tokens, latency

def reflector_real(example: QAExample, attempt_id: int, judge: JudgeResult, answer: str) -> tuple[ReflectionEntry, int, int]:
    context_str = "\n".join([f"Title: {c.title}\nText: {c.text}" for c in example.context])
    user_prompt = f"Context:\n{context_str}\n\nQuestion: {example.question}\nPredicted Answer: {answer}\nEvaluator Reason: {judge.reason}"
    
    content, tokens, latency = call_llm(REFLECTOR_SYSTEM, user_prompt)
    
    parsed = parse_json_from_text(content)
    lesson = parsed.get("lesson", "Failed to parse Reflector JSON.")
    strategy = parsed.get("next_strategy", "Failed to parse Reflector JSON.")
    
    return ReflectionEntry(
        attempt_id=attempt_id,
        failure_reason=judge.reason,
        lesson=lesson,
        next_strategy=strategy
    ), tokens, latency
