from typing import Generator, Optional
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)

WRITER_SYSTEM_PROMPT = """You are an expert Research Writer who synthesises complex information 
into clear, accurate, and well-structured responses. Your guidelines:

1. Write in a clear, engaging style appropriate for an intelligent general audience.
2. Structure responses with a direct answer first, then supporting details.
3. Use markdown formatting: headings, bullet points, bold for key terms.
4. Always cite sources inline using [Source N] notation.
5. Include a brief confidence assessment at the end.
6. Highlight any important caveats or limitations.
7. Keep responses concise but comprehensive — quality over quantity.

Format your response as:
## Answer
[Direct, concise answer to the question]

## Details
[Supporting information, context, and evidence]

## Sources
[Numbered list of sources used]

## Confidence
[Your confidence level and reasoning]
"""


def write_response(
    query: str,
    research_analysis: str,
    search_results: str,
    client: Optional[OpenAI] = None,
    model: str = "gpt-4o",
) -> str:
    """Generate a well-structured final response from research analysis."""
    if client is None:
        client = OpenAI()

    prompt = f"""Question: {query}

Research Analysis:
{research_analysis}

Raw Search Results (for source citations):
{search_results[:3000]}

Write a comprehensive, well-cited response to the question."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=2000,
        )
        content = response.choices[0].message.content
        logger.info(f"Writer agent completed for: {query[:60]}")
        return content
    except Exception as e:
        logger.error(f"Writer agent error: {e}")
        return f"Unable to generate response: {e}"


def write_response_stream(
    query: str,
    research_analysis: str,
    search_results: str,
    client: Optional[OpenAI] = None,
    model: str = "gpt-4o",
) -> Generator[str, None, None]:
    """Stream the final response token by token."""
    if client is None:
        client = OpenAI()

    prompt = f"""Question: {query}

Research Analysis:
{research_analysis}

Raw Search Results (for source citations):
{search_results[:3000]}

Write a comprehensive, well-cited response to the question."""

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": WRITER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=2000,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.error(f"Writer stream error: {e}")
        yield f"\n\n⚠️ Streaming error: {e}"
