"""
Command Line Interface for Quanteinstein B2B Outbound Intelligence Engine.
"""

import sys
import json
import asyncio
import csv
import argparse
from colorama import init, Fore, Style
from app.config import settings
from app.models import ProspectInput
from app.analyzer import B2BIntelligenceAnalyzer
from app.storage import ProspectStorage

init(autoreset=True)


def print_banner():
    banner = f"""
{Fore.CYAN}========================================================================
   QUANTEINSTEIN  |  B2B OUTBOUND INTELLIGENCE & INTENT SCORING ENGINE
   Audience: Prop Desks, Emerging Hedge Funds, Systematic Quants
========================================================================{Style.RESET_ALL}
"""
    print(banner)


def format_result_card(record):
    score = record.score
    color = Fore.GREEN if score >= 8 else (Fore.YELLOW if score >= 4 else Fore.RED)
    
    print("\n" + "-" * 70)
    print(f"PROSPECT: {Fore.WHITE}{record.name} {Fore.LIGHTBLACK_EX}({record.title} @ {record.company}){Style.RESET_ALL}")
    print(f"INTENT SCORE: {color}{record.score} / 10  [{record.intent_tier}]{Style.RESET_ALL}")
    print(f"REASONING: {Fore.LIGHTWHITE_EX}{record.reasoning}{Style.RESET_ALL}")
    
    if record.triggers:
        print(f"TRIGGERS IDENTIFIED:")
        for t in record.triggers:
            print(f"  • {Fore.CYAN}[{t.category.upper()}]{Style.RESET_ALL} {t.signal}")

    if record.message:
        print(f"\n{Fore.GREEN}DRAFTED CONNECTION REQUEST ({record.word_count} words / max {settings.MAX_MESSAGE_WORDS}):{Style.RESET_ALL}")
        print(f"{Fore.WHITE}\"{record.message}\"{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.LIGHTBLACK_EX}NO MESSAGE DRAFTED (Score < {settings.MIN_SCORE_FOR_OUTREACH} -> PASS){Style.RESET_ALL}")
    print("-" * 70 + "\n")


async def run_single_analysis(bio: str, posts: str, jobs: str, name: str = "Prospect", company: str = "", title: str = "", strict: bool = False):
    analyzer = B2BIntelligenceAnalyzer()
    storage = ProspectStorage()
    
    prospect = ProspectInput(
        name=name,
        company=company,
        title=title,
        scraped_profile_bio=bio,
        recent_posts_and_comments=posts,
        recent_company_job_listings=jobs
    )
    
    record = await analyzer.analyze_prospect(prospect)
    storage.save_prospect(record)
    
    if strict:
        # Output ONLY the strict JSON format specified in the prompt
        strict_json = analyzer.to_strict_json(record)
        print(json.dumps(strict_json, indent=2))
    else:
        format_result_card(record)


async def run_batch_file(filepath: str, output_file: str = None):
    analyzer = B2BIntelligenceAnalyzer()
    storage = ProspectStorage()
    
    print(f"{Fore.CYAN}Loading batch from: {filepath}{Style.RESET_ALL}")
    
    prospects = []
    if filepath.endswith(".json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                prospects.append(ProspectInput(**item))
    elif filepath.endswith(".csv"):
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                prospects.append(ProspectInput(
                    name=row.get("name", f"Lead #{idx+1}"),
                    company=row.get("company", ""),
                    title=row.get("title", ""),
                    linkedin_url=row.get("linkedin_url", ""),
                    scraped_profile_bio=row.get("scraped_profile_bio", ""),
                    recent_posts_and_comments=row.get("recent_posts_and_comments", ""),
                    recent_company_job_listings=row.get("recent_company_job_listings", "")
                ))
    else:
        print(f"{Fore.RED}Unsupported file format. Provide .json or .csv{Style.RESET_ALL}")
        return

    print(f"Processing {len(prospects)} prospects...\n")
    results = []
    for p in prospects:
        rec = await analyzer.analyze_prospect(p)
        storage.save_prospect(rec)
        results.append(rec)
        format_result_card(rec)

    high_intent = [r for r in results if r.score >= 8]
    print(f"\n{Fore.GREEN}BATCH SUMMARY:{Style.RESET_ALL}")
    print(f"Total Processed: {len(results)}")
    print(f"High Intent (Score >= 8): {len(high_intent)} ({round(len(high_intent)/len(results)*100, 1) if results else 0}%)")
    print(f"Passed: {len(results) - len(high_intent)}")

    if output_file:
        out_data = [analyzer.to_strict_json(r) for r in results]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2)
        print(f"{Fore.CYAN}Saved strict results to: {output_file}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(description="Quanteinstein B2B Outbound Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Command: analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze a single prospect")
    p_analyze.add_argument("--bio", default="", help="Scraped profile bio")
    p_analyze.add_argument("--posts", default="", help="Recent posts and comments")
    p_analyze.add_argument("--jobs", default="", help="Recent company job listings")
    p_analyze.add_argument("--name", default="Prospect", help="Prospect full name")
    p_analyze.add_argument("--company", default="", help="Prospect company")
    p_analyze.add_argument("--title", default="", help="Prospect title")
    p_analyze.add_argument("--strict", action="store_true", help="Output strict JSON format only")

    # Command: batch
    p_batch = subparsers.add_parser("batch", help="Batch analyze prospects from CSV or JSON")
    p_batch.add_argument("--file", required=True, help="Input JSON or CSV file path")
    p_batch.add_argument("--out", default=None, help="Output JSON file path")

    # Command: stats
    p_stats = subparsers.add_parser("stats", help="Show system and lead stats")

    # Command: interactive
    p_inter = subparsers.add_parser("interactive", help="Interactive prompt to input scraped data")

    args = parser.parse_args()

    if args.command == "analyze":
        asyncio.run(run_single_analysis(
            bio=args.bio,
            posts=args.posts,
            jobs=args.jobs,
            name=args.name,
            company=args.company,
            title=args.title,
            strict=args.strict
        ))
    elif args.command == "batch":
        print_banner()
        asyncio.run(run_batch_file(args.file, args.out))
    elif args.command == "stats":
        print_banner()
        storage = ProspectStorage()
        stats = storage.get_stats()
        print(f"Total Prospects Evaluated: {stats.total_analyzed}")
        print(f"High-Intent Leads (>=8):  {stats.tier_high_intent}")
        print(f"Qualified ICP Passes:     {stats.tier_qualified_pass}")
        print(f"Irrelevant Passes:        {stats.tier_irrelevant}")
        print(f"Messages Drafted:         {stats.messages_drafted}")
        print(f"Average Intent Score:     {stats.average_score} / 10")
    elif args.command == "interactive":
        print_banner()
        print("Enter scraped prospect data (leave blank for defaults):")
        name = input("Prospect Name: ").strip() or "Prospect"
        company = input("Company: ").strip() or ""
        title = input("Title: ").strip() or ""
        print("\nPaste Scraped Bio:")
        bio = input("> ").strip()
        print("\nPaste Recent Posts & Comments:")
        posts = input("> ").strip()
        print("\nPaste Recent Company Job Listings:")
        jobs = input("> ").strip()
        asyncio.run(run_single_analysis(bio, posts, jobs, name, company, title))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
