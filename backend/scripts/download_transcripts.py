"""
Dynamic Transcript Downloader for The Lenny Growth Assistant.

Discovers ALL available episodes from the ChatPRD/lennys-podcast-transcripts
GitHub repository via the GitHub API, then downloads each transcript.md file.
"""
import os
import sys
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("download-transcripts")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "data", "transcripts")

GITHUB_API_URL = "https://api.github.com/repos/ChatPRD/lennys-podcast-transcripts/contents/episodes"
RAW_BASE_URL = "https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main/episodes"


def discover_episodes(client) -> list:
    """Discover all episode slugs from the GitHub API."""
    logger.info(f"Discovering episodes from {GITHUB_API_URL}...")
    try:
        resp = client.get(GITHUB_API_URL)
        if resp.status_code == 200:
            entries = resp.json()
            # Filter to directories only
            slugs = [e["name"] for e in entries if e.get("type") == "dir"]
            logger.info(f"Discovered {len(slugs)} episode directories from GitHub.")
            return slugs
        elif resp.status_code == 403:
            logger.warning("GitHub API rate limit reached. Using fallback episode list.")
            return []
        else:
            logger.warning(f"GitHub API returned {resp.status_code}. Using fallback episode list.")
            return []
    except Exception as e:
        logger.warning(f"Failed to query GitHub API ({e}). Using fallback episode list.")
        return []


# Fallback list of known episodes (the original 6 + additional well-known guests)
FALLBACK_EPISODES = [
    "adam-fishman", "elena-verna", "shreyas-doshi",
    "brian-chesky", "julie-zhuo", "gustaf-alstromer",
]


def download_all():
    """Download all available transcripts from the ChatPRD repository."""
    import httpx

    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
    logger.info(f"Target directory: {TRANSCRIPTS_DIR}")

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        # Step 1: Discover episodes dynamically
        slugs = discover_episodes(client)
        if not slugs:
            slugs = FALLBACK_EPISODES
            logger.info(f"Using fallback list of {len(slugs)} episodes.")

        downloaded = 0
        skipped = 0
        failed = 0

        for i, slug in enumerate(slugs, 1):
            target_path = os.path.join(TRANSCRIPTS_DIR, f"{slug}.md")

            # Skip if already downloaded and has substantial content
            if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
                skipped += 1
                continue

            url = f"{RAW_BASE_URL}/{slug}/transcript.md"
            logger.info(f"[{i}/{len(slugs)}] Downloading {slug}...")

            try:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.text) > 500:
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(resp.text)
                    downloaded += 1
                    logger.info(f"  Saved {slug}.md ({len(resp.text):,} chars)")
                elif resp.status_code == 404:
                    # Try alternate filename patterns
                    alt_url = f"{RAW_BASE_URL}/{slug}/transcript.txt"
                    alt_resp = client.get(alt_url)
                    if alt_resp.status_code == 200 and len(alt_resp.text) > 500:
                        with open(target_path, "w", encoding="utf-8") as f:
                            f.write(alt_resp.text)
                        downloaded += 1
                        logger.info(f"  Saved {slug}.md from .txt ({len(alt_resp.text):,} chars)")
                    else:
                        failed += 1
                        logger.warning(f"  No transcript found for {slug} (404)")
                else:
                    failed += 1
                    logger.warning(f"  Failed to fetch {slug}: HTTP {resp.status_code}")
            except Exception as e:
                failed += 1
                logger.error(f"  Error fetching {slug}: {e}")

            # Respect GitHub rate limits with a small delay
            if i % 20 == 0:
                time.sleep(1.0)

        logger.info(f"\nDownload Summary:")
        logger.info(f"  Downloaded: {downloaded}")
        logger.info(f"  Skipped (already exist): {skipped}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Total episodes available: {len(slugs)}")
        logger.info(f"  Total transcripts on disk: {len([f for f in os.listdir(TRANSCRIPTS_DIR) if f.endswith('.md')])}")


if __name__ == "__main__":
    download_all()
