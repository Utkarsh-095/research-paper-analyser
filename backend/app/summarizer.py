"""Summarization engine using Groq / OpenAI."""

from typing import Dict
from openai import OpenAI
from .config import settings


class Summarizer:
    def __init__(self):
        self.client = None
        if settings.openai_api_key and "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" not in settings.openai_api_key:
            self.client = OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )

    def summarize(self, text: str, title: str = "") -> Dict[str, str]:
        """Generate a summary and extract key findings."""
        if self.client:
            try:
                return self._ai_summarize(text, title)
            except Exception as e:
                print(f"[Summarizer Error] Falling back to extractive mode: {e}")
                return self._extractive_summarize(text)
        return self._extractive_summarize(text)

    def _ai_summarize(self, text: str, title: str) -> Dict[str, str]:
        # Limit text length to avoid token limits
        max_chars = 15000
        truncated = text[:max_chars]

        summary_prompt = f"""You are an academic research expert.
Analyze this research paper titled "{title}" and provide:

1. SUMMARY: A concise 2-3 paragraph overview of the paper's objective, methodology, and key results.
2. KEY FINDINGS: 5 distinct bullet points highlighting key insights, discoveries, or numbers.

Paper Content:
{truncated}

Respond in this exact format:
SUMMARY:
[summary text]

KEY FINDINGS:
- [finding 1]
- [finding 2]
- [finding 3]
- [finding 4]
- [finding 5]"""

        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a research paper analysis assistant."},
                {"role": "user", "content": summary_prompt},
            ],
            max_tokens=1000,
            temperature=0.3,
        )

        content = response.choices[0].message.content
        return self._parse_response(content)

    def _extractive_summarize(self, text: str) -> Dict[str, str]:
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 50]
        summary_sentences = sentences[: min(6, len(sentences))]
        summary = ". ".join(summary_sentences) + "."

        key_findings = []
        keywords = ["we found", "results show", "we demonstrate", "we propose", "significant", "novel", "accuracy"]
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords):
                key_findings.append(sentence.strip())
                if len(key_findings) >= 5:
                    break

        return {
            "summary": summary,
            "key_findings": "\n".join(f"- {f}" for f in key_findings) if key_findings else "- Findings extracted from paper text.",
        }

    @staticmethod
    def _parse_response(content: str) -> Dict[str, str]:
        summary = ""
        key_findings = ""
        if "KEY FINDINGS:" in content:
            parts = content.split("KEY FINDINGS:")
            summary = parts[0].replace("SUMMARY:", "").strip()
            key_findings = parts[1].strip()
        elif "SUMMARY:" in content:
            summary = content.replace("SUMMARY:", "").strip()
        else:
            summary = content.strip()
        return {"summary": summary, "key_findings": key_findings}


summarizer = Summarizer()