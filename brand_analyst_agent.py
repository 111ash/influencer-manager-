"""
brand_analyst_agent.py — Dynamic Brand Analysis Agent.

Analyzes the user's provided channel description or bio to generate a tailored
CREATOR_STYLE profile using heuristic keyword matching.
"""

from __future__ import annotations
import config

import urllib.request
import re

_CYAN = "\033[96m"
_GREEN = "\033[92m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_BOLD = "\033[1m"
_YELLOW = "\033[93m"

def _fetch_profile_bio(url: str) -> tuple[str, int]:
    """
    Fetch profile data from a URL.
    
    Returns:
        tuple: (bio_text, video_count)
            - bio_text:    Combined text from RSS titles/descriptions + meta description.
            - video_count: Number of actual videos found via RSS (0 if none).
    """
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        
        # Try to extract RSS feed link for deeper analysis
        rss_match = re.search(r'<link\s+rel=["\']alternate["\']\s+type=["\']application/rss\+xml["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        
        corpus = []
        video_count = 0
        
        if rss_match:
            rss_url = rss_match.group(1).strip()
            print(f"  {_DIM}Found RSS feed, fetching recent video metadata...{_RESET}")
            try:
                rss_req = urllib.request.Request(
                    rss_url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                rss_xml = urllib.request.urlopen(rss_req, timeout=5).read().decode('utf-8', errors='ignore')
                
                # Extract video titles (skip the first — it's the channel name)
                titles = re.findall(r'<title>(.*?)</title>', rss_xml, re.IGNORECASE)
                if len(titles) > 1:
                    video_titles = titles[1:]
                    video_count = len(video_titles)
                    corpus.extend(video_titles)
                
                # Extract video descriptions
                descriptions = re.findall(r'<media:description[^>]*>(.*?)</media:description>', rss_xml, re.IGNORECASE | re.DOTALL)
                corpus.extend(descriptions)
                
                print(f"  {_DIM}Found {video_count} video(s) to analyze.{_RESET}")
            except Exception as e:
                print(f"  {_YELLOW}⚠ Failed to fetch RSS feed ({e}).{_RESET}")

        # Try to extract meta description (often contains subscriber counts)
        meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if meta_match:
            desc = meta_match.group(1).strip()
            if len(desc) > 10:
                corpus.append(desc)
                
        if not corpus:
            # Fallback to page title
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title_match:
                corpus.append(title_match.group(1).strip())
                
        if corpus:
            return (" ".join(corpus), video_count)
            
    except Exception as e:
        print(f"  {_YELLOW}⚠ Failed to fetch profile data ({e}).{_RESET}")
        
    return ("", 0)


def _extract_and_update_metrics(url: str, text: str) -> None:
    """Extracts follower/subscriber counts from text and updates config."""
    # Matches patterns like "500K Followers", "1.5M subscribers", "1,200 subs"
    match = re.search(r'([\d.,]+)([kKmM]?)\s*(?:Followers|Subscribers|followers|subscribers|Subs|subs)', text)
    if not match:
        return
        
    num_str = match.group(1).replace(',', '')
    try:
        base_val = float(num_str)
    except ValueError:
        return
        
    multiplier = match.group(2).upper()
    if multiplier == 'K':
        base_val *= 1000
    elif multiplier == 'M':
        base_val *= 1000000
        
    count = int(base_val)
    
    if "youtube.com" in url.lower():
        config.PLATFORMS["YouTube"]["subscribers"] = count
        print(f"  {_GREEN}✓ Extracted {count:,} YouTube subscribers from profile.{_RESET}")
    elif "instagram.com" in url.lower():
        config.PLATFORMS["Instagram"]["followers"] = count
        print(f"  {_GREEN}✓ Extracted {count:,} Instagram followers from profile.{_RESET}")
    elif "tiktok.com" in url.lower():
        config.PLATFORMS["TikTok"]["followers"] = count
        print(f"  {_GREEN}✓ Extracted {count:,} TikTok followers from profile.{_RESET}")


def analyze_brand() -> None:
    """Prompts user for name and bio, and updates config dynamically."""
    print(f"\n  {_CYAN}{_BOLD}🔍 CREATOR ONBOARDING & BRAND ANALYSIS{_RESET}")
    print(f"  {_CYAN}Let's set up your personal brand profile.{_RESET}")
    
    try:
        name = input(f"  {_BOLD}What is your name or channel alias? {_RESET}").strip()
        print(f"  {_DIM}(e.g., 'I make cozy tech reviews', or paste a YouTube/Instagram profile URL){_RESET}")
        bio = input(f"  {_BOLD}Describe your brand or paste a profile URL: {_RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        name = ""
        bio = ""
        
    if name:
        config.CREATOR_NAME = name
        
    if not bio:
        print(f"  {_YELLOW}No bio provided. Using default style settings for {config.CREATOR_NAME}.{_RESET}\n")
        return
        
    # Check if the user pasted a URL
    if bio.startswith("http") or "www." in bio or ".com" in bio:
        valid_domains = ["youtube.com", "instagram.com", "tiktok.com"]
        if not any(domain in bio for domain in valid_domains):
            print(f"  {_YELLOW}⚠ The link provided is not a recognized YouTube, Instagram, or TikTok profile.{_RESET}")
            print(f"  {_YELLOW}Using default style settings for {config.CREATOR_NAME}.{_RESET}\n")
            return
            
        print(f"  {_DIM}Fetching profile data from URL...{_RESET}")
        url = bio
        bio, video_count = _fetch_profile_bio(url)
        if not bio:
            print(f"  {_YELLOW}Could not extract profile data from link. Using default style settings for {config.CREATOR_NAME}.{_RESET}\n")
            return
        
        # If the link had no videos, there's not enough real content to analyze
        if video_count == 0:
            print(f"  {_YELLOW}⚠ No videos found on this channel. Not enough content to analyze style.{_RESET}")
            print(f"  {_YELLOW}Using default style settings for {config.CREATOR_NAME}.{_RESET}")
            # Still try to extract follower counts from the meta description
            _extract_and_update_metrics(url, bio)
            print()
            return
            
        print(f"  {_DIM}Analyzed {video_count} recent video(s) for style profiling.{_RESET}")
        _extract_and_update_metrics(url, bio)
        
    bio_lower = bio.lower()
    
    # ── Heuristic Analysis (Frequency Scoring) ──
    # Because we now have a large text corpus from RSS, we must score by frequency
    # rather than just checking if a word exists once.
    
    tone_scores = {
        "sarcastic, witty, and humorous": sum(bio_lower.count(k) for k in ["sarcastic", "snarky", "comedy", "funny", "roast"]),
        "calm, cozy, and aesthetic": sum(bio_lower.count(k) for k in ["cozy", "calm", "relax", "chill", "aesthetic", "asmr"]),
        "high-energy, fast-paced, and enthusiastic": sum(bio_lower.count(k) for k in ["hype", "fast", "energetic", "loud", "intense", "insane"]),
        "professional, informative, and clear": sum(bio_lower.count(k) for k in ["pro", "educational", "teach", "serious", "finance", "business", "learn"]),
    }
    
    # Pick the tone with the highest score, default to authentic if all are 0
    best_tone = max(tone_scores, key=tone_scores.get)
    tone = best_tone if tone_scores[best_tone] > 0 else "authentic, engaging, and conversational"

    format_scores = {
        "long-form narrative with deep dives": sum(bio_lower.count(k) for k in ["long", "essay", "documentary", "deep dive", "analysis"]),
        "slow cinematic shots with lo-fi music": sum(bio_lower.count(k) for k in ["cozy", "aesthetic", "cinematic", "vlog", "b-roll"]),
        "fast-paced with aggressive jump cuts and text overlays": sum(bio_lower.count(k) for k in ["fast", "shorts", "tiktok", "adhd", "quick"]),
    }
    best_format = max(format_scores, key=format_scores.get)
    fmt = best_format if format_scores[best_format] > 0 else "well-paced with B-roll cutaways"

    intro_outro_scores = {
        "gaming": sum(bio_lower.count(k) for k in ["gaming", "gameplay", "stream", "lobby", "esports", "twitch"]),
        "tech": sum(bio_lower.count(k) for k in ["tech", "review", "gadget", "software", "apple", "setup"]),
        "cozy": sum(bio_lower.count(k) for k in ["cozy", "vlog", "day in the life", "morning routine", "aesthetic"]),
        "finance": sum(bio_lower.count(k) for k in ["finance", "invest", "money", "business", "crypto", "stock"]),
    }
    best_io = max(intro_outro_scores, key=intro_outro_scores.get)
    
    first_name = config.CREATOR_NAME.split()[0]
    if intro_outro_scores[best_io] > 0:
        if best_io == "gaming":
            intro = f"What's up gamers, {first_name} here!"
            outro = "Don't forget to like and subscribe, catch you in the next lobby! ✌️"
            email_sign = "Cheers,"
        elif best_io == "tech":
            intro = f"Hey everyone, welcome back. {first_name} here."
            outro = "Let me know your thoughts in the comments down below. See ya! 👋"
            email_sign = "Best,"
        elif best_io == "cozy":
            intro = "Hello friends, welcome back to another cozy day..."
            outro = "Take care of yourselves, and I'll see you in the next one. ☁️"
            email_sign = "Warmly,"
        elif best_io == "finance":
            intro = f"Welcome back. I'm {first_name}, let's talk numbers."
            outro = "Hit the like button for the YouTube algorithm, and stay wealthy! 📈"
            email_sign = "Regards,"
    else:
        intro = f"Hey guys, {first_name} here!"
        outro = "Drop a comment if you learned something — bye! ✌️"
        email_sign = "Best,"
        
    # Update the config dynamically
    config.CREATOR_STYLE["tone"] = tone
    config.CREATOR_STYLE["format"] = fmt
    config.CREATOR_STYLE["signature_intro"] = intro
    config.CREATOR_STYLE["signature_outro"] = outro
    config.CREATOR_STYLE["email_signoff"] = email_sign
    
    print(f"\n  {_GREEN}✓ Brand style analyzed & personalized for {config.CREATOR_NAME}!{_RESET}")
    print(f"    {_DIM}Tone:   {tone}{_RESET}")
    print(f"    {_DIM}Format: {fmt}{_RESET}\n")
