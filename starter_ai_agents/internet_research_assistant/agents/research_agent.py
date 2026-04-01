from typing import Optional
from openai import OpenAI
from utils.helpers import extract_json, score_confidence
from utils.logger import get_logger

logger = get_logger(__name__)

RESEARCH_SYSTEM_PROMPT = """You are a Senior Research Analyst with deep expertise in information 
verification and synthesis. Your responsibilities:

1. Critically analyse search results for accuracy, recency, and relevance.
2. Cross-reference information across multiple sources to verify consistency.
3. Identify conflicting information and flag potential inaccuracies.
4. Prioritise recent, authoritative sources.
5. Extract key facts and evidence that directly answer the user's question.
6. Assess the overall reliability of the gathered information.

Always structure your analysis as:
- KEY FINDINGS: bullet points of verified facts
- CONFIDENCE: High / Medium / Low, with a brief rationale
- CONFLICTS: any contradictions found across sources (if any)
- GAPS: what information is still missing or unclear
"""


def research_and_verify(
    query: str,
    search_results: str,
    client: Optional[OpenAI] = None,
    model: str = "gpt-4o",
) -> dict:
    """
    Analyse and verify search results using an LLM research agent.
    Returns a dict with keys: analysis, confidence, key_facts, gaps.
    """
    if client is None:
        client = OpenAI()

    prompt = f"""Question: {query}

Search Results:
{search_results}

Please analyse these results and provide a structured research assessment."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        analysis = response.choices[0].message.content
        logger.info(f"Research analysis completed for: {query[:60]}")
        return {
            "analysis": analysis,
            "model": model,
            "query": query,
        }
    except Exception as e:
        logger.error(f"Research agent error: {e}")
        return {
            "analysis": f"Research analysis unavailable: {e}",
            "model": model,
            "query": query,
        }


def generate_related_questions(
    query: str,
    answer: str,
    client: Optional[OpenAI] = None,
    model: str = "gpt-4o",
    count: int = 3,
) -> list:
    """Generate related follow-up questions based on the query and answer."""
    if client is None:
        client = OpenAI()

    prompt = f"""Based on the following question and answer, generate {count} insightful 
follow-up questions that would help the user explore the topic further.

Original Question: {query}
Answer Summary: {answer[:500]}

Return ONLY a JSON array of question strings, nothing else.
Example: ["Question 1?", "Question 2?", "Question 3?"]"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
        )
        content = response.choices[0].message.content
        questions = extract_json(content)
        if isinstance(questions, list):
            return questions[:count]
    except Exception as e:
        logger.warning(f"Related questions generation failed: {e}")
    return []
