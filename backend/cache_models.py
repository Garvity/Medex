"""Validate that the runtime has the optional local FlashRank model available.

FlashRank lazily downloads its compact reranker on first use. This script intentionally does
not download external API-backed Jina embedding models because those remain hosted by Jina.
"""

from agent.flashrank_reranker import get_ranker

print("Preparing FlashRank reranker cache...")
get_ranker()
print("FlashRank reranker cache ready.")
