import os
from collections import defaultdict
from decimal import Decimal

from dotenv import load_dotenv
from openai import OpenAI

from .. import models

load_dotenv()

TONE_LABELS = {
    "encouraging": "The Encouraging Mentor",
    "analyst": "The Data-Driven Analyst",
    "blunt": "The Blunt Friend",
    "storyteller": "The Storyteller",
}

TONE_INSTRUCTIONS = {
    "encouraging": (
        "Write as a warm, encouraging mentor. Celebrate small wins, be gentle "
        "about overspending, and end with one concrete, achievable suggestion."
    ),
    "analyst": (
        "Write as a precise, data-driven analyst. Reference specific numbers "
        "and percentages, keep emotion out of it, and end with a ranked list "
        "of the top 3 optimization opportunities."
    ),
    "blunt": (
        "Write as a blunt, no-nonsense friend. Be direct and a little witty "
        "about wasteful spending, but never mean-spirited. End with one hard "
        "truth the user needs to hear."
    ),
    "storyteller": (
        "Write as a storyteller narrating the user's month as a short "
        "narrative arc with a beginning, tension, and resolution, using "
        "their spending as plot points. Keep it vivid but grounded in the "
        "real numbers."
    ),
}

SYSTEM_PROMPT = (
    "You are the narrative engine inside a personal finance app called "
    "MoneyNarrator. You turn a user's raw transaction data into a short, "
    "human, readable financial report (250-400 words). Never invent numbers "
    "that aren't implied by the data given. Use markdown with a short title "
    "and 2-4 short paragraphs or bullet points."
)


class NoTransactionsError(Exception):
    """Raised when there is nothing to summarize."""


def _summarize(transactions: list[models.Transaction]) -> dict:
    total_income = Decimal("0")
    total_expense = Decimal("0")
    by_category: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for t in transactions:
        if t.type == "income":
            total_income += t.amount
        else:
            total_expense += t.amount
            by_category[t.category] += t.amount

    recent = sorted(transactions, key=lambda t: t.txn_date, reverse=True)[:15]

    return {
        "totalIncome": str(total_income),
        "totalExpense": str(total_expense),
        "net": str(total_income - total_expense),
        "spendingByCategory": {k: str(v) for k, v in by_category.items()},
        "transactionCount": len(transactions),
        "recentTransactions": [
            {
                "type": t.type,
                "category": t.category,
                "description": t.description,
                "amount": str(t.amount),
                "date": t.txn_date.isoformat(),
            }
            for t in recent
        ],
    }


def generate_narrative(transactions: list[models.Transaction], tone: str) -> str:
    """Aggregates the user's transactions and asks the AI provider for a
    written report in the requested tone. Raises NoTransactionsError if
    there's nothing to summarize.
    """
    if not transactions:
        raise NoTransactionsError()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENROUTER_API_KEY. Add it to your .env file."
        )

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    summary = _summarize(transactions)
    tone_label = TONE_LABELS.get(tone, TONE_LABELS["encouraging"])
    tone_instructions = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["encouraging"])

    user_prompt = (
        f"Persona for this report: {tone_label}.\n"
        f"Tone instructions: {tone_instructions}\n\n"
        f"Here is the user's financial data as JSON:\n{summary}\n\n"
        "Write the report now."
    )

    completion = client.chat.completions.create(
        model="openrouter/free",
        max_tokens=700,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return completion.choices[0].message.content or ""
