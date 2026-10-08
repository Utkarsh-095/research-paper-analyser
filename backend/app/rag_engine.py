"""RAG Engine for Q&A using Groq / OpenAI."""

from typing import Dict, List
from openai import OpenAI
from .config import settings
from .vector_store import vector_store


class RAGEngine:
    def __init__(self):
        self.client = None
        key = settings.openai_api_key.strip() if settings.openai_api_key else ""

        if not key:
            print("⚠️  [RAG] No API key found — Q&A will only return raw passages.")
        elif "PASTE_YOUR" in key:
            print("⚠️  [RAG] API key is still the placeholder! Put your real Groq key in config.py")
        else:
            self.client = OpenAI(
                api_key=key,
                base_url=settings.openai_base_url,
            )
            print(f"✅ [RAG] LLM client initialized → model: {settings.openai_model}")

    def answer_question(
        self,
        collection_name: str,
        question: str,
        paper_title: str = "",
        top_k: int = settings.top_k_results,
    ) -> Dict:
        relevant_chunks = vector_store.query(collection_name, question, n_results=top_k)

        if not relevant_chunks:
            return {
                "answer": "I couldn't find any relevant passages in this paper to answer that question.",
                "sources": [],
                "confidence": 0.0,
            }

        context = self._build_context(relevant_chunks)

        if self.client:
            try:
                print(f"🤖 [RAG] Sending question to {settings.openai_model}...")
                answer = self._generate_ai_answer(question, context, paper_title)
                print("✅ [RAG] LLM answer received")
            except Exception as e:
                print(f"❌ [RAG] LLM CALL FAILED: {type(e).__name__}: {e}")
                answer = (
                    f"⚠️ LLM Error: {str(e)}\n\n"
                    + self._generate_extractive_answer(relevant_chunks)
                )
        else:
            answer = self._generate_extractive_answer(relevant_chunks)

        avg_similarity = sum(c["similarity"] for c in relevant_chunks) / len(relevant_chunks)

        sources = [
            {
                "text": chunk["text"][:300] + "..." if len(chunk["text"]) > 300 else chunk["text"],
                "chunk_index": chunk["metadata"].get("chunk_index", 0),
                "similarity": round(chunk["similarity"], 4),
            }
            for chunk in relevant_chunks
        ]

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(avg_similarity, 4),
        }

    @staticmethod
    def _build_context(chunks: List[Dict]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[Source {i}]:\n{chunk['text']}")
        return "\n\n---\n\n".join(parts)

    def _generate_ai_answer(self, question: str, context: str, title: str) -> str:
        prompt = f"""You are an expert assistant answering questions about the research paper "{title}".

Use ONLY the excerpts below to answer. Synthesize a clear, direct answer in your own words — do NOT just copy the passages.

Rules:
1. Answer the question directly in the first sentence.
2. Then explain with supporting details from the context.
3. Cite sources like [Source 1], [Source 2] where used.
4. If the context lacks the answer, say: "The paper does not directly address this."

Context:
{context}

Question: {question}

Answer:"""

        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a precise academic research assistant who gives direct, synthesized answers — never raw text dumps."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    @staticmethod
    def _generate_extractive_answer(chunks: List[Dict]) -> str:
        parts = ["Here are the most relevant excerpts found in the paper:\n"]
        for i, chunk in enumerate(chunks[:3], 1):
            parts.append(f"\n**[Source {i}]** (Relevance: {chunk['similarity']:.1%}):\n{chunk['text'][:400]}...")
        return "\n".join(parts)


rag_engine = RAGEngine()