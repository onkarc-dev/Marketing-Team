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
from app.models import ProspectInput, SearchQueryRequest
from app.analyzer import B2BIntelligenceAnalyzer
from app.storage import ProspectStorage
from app.discovery import WebDiscoveryEngine
from app.email_generator import EmailOutreachGenerator

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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


async def run_regional_prospecting(niche: str, region: str, firm_type: str = "emerging hedge fund", count: int = 5, sender: str = None, out_file: str = None, send_now: bool = False):
    sender_name = sender or getattr(settings, "SENDER_NAME", "Onkar (Founder, Quanteinstein)")

    print_banner()
    print(f"{Fore.CYAN}[*] Initiating Agent Web Search & Lead Intelligence:{Style.RESET_ALL}")
    print(f"  * Niche:  {Fore.WHITE}{niche}{Style.RESET_ALL}")
    print(f"  * Region: {Fore.GREEN}{region}{Style.RESET_ALL}")
    print(f"  * Target: {Fore.YELLOW}{firm_type}{Style.RESET_ALL}")
    print(f"  * Target Count: {count}\n")

    discovery = WebDiscoveryEngine()
    generator = EmailOutreachGenerator()

    req = SearchQueryRequest(niche=niche, region=region, firm_type=firm_type, num_results=count, sender_name=sender)
    leads = await discovery.search_and_discover(req)

    print(f"{Fore.GREEN}[+] Discovered {len(leads)} matching firms with validated contact channels.{Style.RESET_ALL}\n")

    generated_emails = []
    for idx, lead in enumerate(leads, 1):
        print(f"{Fore.CYAN}[{idx}/{len(leads)}] Analyzing {lead.firm_name} ({lead.region})...{Style.RESET_ALL}")
        print(f"  Website: {lead.website} | Email: {Fore.YELLOW}{lead.email}{Style.RESET_ALL}")
        print(f"  Focus:   {', '.join(lead.strategies_detected)}")
        
        email = await generator.generate_email(lead, sender_name=sender)
        generated_emails.append(email)

        print(f"\n{Fore.GREEN}---------------- DRAFTED PROPER COLD EMAIL ({email.word_count} words) ----------------{Style.RESET_ALL}")
        print(f"{Fore.CYAN}To:{Style.RESET_ALL}      {email.recipient_email} ({email.recipient_name})")
        print(f"{Fore.CYAN}Subject:{Style.RESET_ALL} {Fore.WHITE}{email.subject}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Body:{Style.RESET_ALL}\n{email.body}")
        print(f"{Fore.GREEN}----------------------------------------------------------------------{Style.RESET_ALL}\n")

        if send_now:
            from app.email_sender import EmailDispatcher
            print(f"{Fore.YELLOW}[*] Sending email to {email.recipient_email} via local SMTP...{Style.RESET_ALL}")
            dispatch_res = EmailDispatcher.send_email(
                recipient_email=email.recipient_email,
                subject=email.subject,
                body=email.body
            )
            if dispatch_res.get("success"):
                print(f"{Fore.GREEN}[+] {dispatch_res.get('message')}{Style.RESET_ALL}\n")
            else:
                print(f"{Fore.RED}[-] {dispatch_res.get('message')}{Style.RESET_ALL}\n")

    if out_file:
        out_dicts = [e.model_dump() for e in generated_emails]
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out_dicts, f, indent=2)
        print(f"{Fore.CYAN}Saved all drafted emails to: {out_file}{Style.RESET_ALL}")


def run_test_smtp():
    print_banner()
    print(f"{Fore.CYAN}[*] Testing Local SMTP Email Connection...{Style.RESET_ALL}")
    from app.email_sender import EmailDispatcher
    result = EmailDispatcher.test_connection()
    if result.get("connected"):
        print(f"{Fore.GREEN}[+] SUCCESS: {result.get('message')}{Style.RESET_ALL}")
        print(f"    Account: {result.get('user')}")
        print(f"    Server:  {result.get('host')}:{result.get('port')}")
        print(f"{Fore.CYAN}[*] Your email account is connected and ready to send outreach!{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}[-] CONNECTION FAILED: {result.get('message')}{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Setup Instructions for Personal Gmail/Outlook:{Style.RESET_ALL}")
        print("  1. Gmail requires a Google App Password (not your normal password).")
        print("  2. Turn on 2-Step Verification at: https://myaccount.google.com/signinoptions/two-step-verification")
        print("  3. Create an App Password at: https://myaccount.google.com/apppasswords")
        print("  4. Open .env in this folder and set:")
        print("       SMTP_HOST=smtp.gmail.com")
        print("       SMTP_PORT=587")
        print("       SMTP_USER=your_email@gmail.com")
        print("       SMTP_PASSWORD=your_16_char_app_password")
        print("  5. Re-run: python main.py test-smtp\n")


def run_cli_send_email(to: str, subject: str, body: str):
    from app.email_sender import EmailDispatcher
    print(f"{Fore.CYAN}[*] Sending email to {to}...{Style.RESET_ALL}")
    res = EmailDispatcher.send_email(recipient_email=to, subject=subject, body=body)
    if res.get("success"):
        print(f"{Fore.GREEN}[+] {res.get('message')}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[-] {res.get('message')}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(description="Quanteinstein B2B Outbound Intelligence CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Command: prospect (Web Search + Email Generation)
    p_prospect = subparsers.add_parser("prospect", help="Search web by region & niche, scrape emails, and write cold outreach")
    p_prospect.add_argument("--region", default="London, UK", help="Target region/city/area")
    p_prospect.add_argument("--niche", default="quantitative hedge fund", help="Target trading niche")
    p_prospect.add_argument("--firm-type", default="emerging hedge fund", help="Firm stage or type")
    p_prospect.add_argument("--count", type=int, default=3, help="Number of firms to research")
    p_prospect.add_argument("--sender", default=getattr(settings, "SENDER_NAME", "Onkar (Founder, Quanteinstein)"), help="Sender name for email signature")
    p_prospect.add_argument("--out", default=None, help="Output JSON path to save emails")

    p_prospect.add_argument("--send", action="store_true", help="Directly send emails via SMTP after drafting")

    # Command: test-smtp
    subparsers.add_parser("test-smtp", help="Test local email connection (Gmail / Outlook / Custom SMTP)")

    # Command: send-email
    p_send = subparsers.add_parser("send-email", help="Send a single email via configured SMTP")
    p_send.add_argument("--to", required=True, help="Recipient email address")
    p_send.add_argument("--subject", required=True, help="Email subject line")
    p_send.add_argument("--body", required=True, help="Email body content")

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
    elif args.command == "prospect":
        asyncio.run(run_regional_prospecting(
            niche=args.niche,
            region=args.region,
            firm_type=args.firm_type,
            count=args.count,
            sender=args.sender,
            out_file=args.out,
            send_now=args.send
        ))
    elif args.command == "test-smtp":
        run_test_smtp()
    elif args.command == "send-email":
        run_cli_send_email(args.to, args.subject, args.body)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

