#!/usr/bin/env python3
"""
Database Router

Routes database files to appropriate extraction method based on identification.
Decision flow: DBeaver CLI (if supported) → db-extractor-* skill (if not)

Usage:
    python db_route.py --format sqlite --dbeaver-supported true
    python db_route.py --json '{"format": "sqlite", "dbeaver_supported": true}'
    python db_route.py --file database.db  # runs identification internally
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Routing table: format → extractor skill
EXTRACTOR_SKILLS = {
    "sqlite": "db-extractor-sqlite",
    "mysql": "db-extractor-mysql",
    "access": "db-extractor-access",
    "dbf": "db-extractor-dbf",
    "h2": "db-extractor-h2",
    "firebird": "db-extractor-firebird",
    "berkeleydb": "db-extractor-berkeleydb",
    "redis-rdb": "db-extractor-redis",
    "derby": "db-extractor-derby",
}

# Skill availability (which ones are implemented)
SKILL_STATUS = {
    "db-extractor-sqlite": "available",
    "db-extractor-mysql": "available",
    "db-extractor-access": "planned",
    "db-extractor-dbf": "planned",
    "db-extractor-h2": "planned",
    "db-extractor-firebird": "planned",
    "db-extractor-berkeleydb": "planned",
    "db-extractor-redis": "planned",
    "db-extractor-derby": "planned",
}


def route(format: str, dbeaver_supported: bool = None, confidence: str = "high") -> dict:
    """
    Determine extraction route based on format identification.
    
    Args:
        format: Database format (e.g., "sqlite", "access")
        dbeaver_supported: Whether DBeaver CLI supports this format
        confidence: Detection confidence ("high", "low", "none")
        
    Returns:
        Routing decision with method and instructions
    """
    if format == "unknown" or format is None:
        return {
            "decision": "unknown_format",
            "method": None,
            "instructions": [
                "Format could not be identified",
                "Try opening with DBeaver GUI to identify",
                "Check file documentation or source",
            ],
        }
    
    skill = EXTRACTOR_SKILLS.get(format)
    skill_status = SKILL_STATUS.get(skill, "unavailable")
    
    # Decision logic: prefer DBeaver if supported, else use skill
    if dbeaver_supported:
        return {
            "decision": "use_dbeaver",
            "method": "dbeaver_cli",
            "format": format,
            "fallback_skill": skill,
            "fallback_status": skill_status,
            "instructions": [
                f"Use DBeaver CLI to export {format} database",
                "DBeaver supports this format natively",
                f"Fallback: {skill} ({skill_status})" if skill else "No fallback skill available",
            ],
            "dbeaver_export_hint": get_dbeaver_hint(format),
        }
    else:
        if skill_status == "available":
            return {
                "decision": "use_skill",
                "method": "extractor_skill",
                "skill": skill,
                "skill_status": skill_status,
                "format": format,
                "instructions": [
                    f"DBeaver CLI does not support {format}",
                    f"Use {skill} for extraction",
                ],
            }
        else:
            return {
                "decision": "skill_needed",
                "method": None,
                "skill": skill,
                "skill_status": skill_status,
                "format": format,
                "instructions": [
                    f"DBeaver CLI does not support {format}",
                    f"Extractor skill {skill} is {skill_status}",
                    "Need to create extraction skill for this format",
                ],
            }


def get_dbeaver_hint(format: str) -> str:
    """Get DBeaver CLI export hint for format."""
    hints = {
        "sqlite": "dbeaver-cli -c 'SELECT * FROM table' -d sqlite:///path/to/db.sqlite",
        "mysql": "dbeaver-cli -c 'SELECT * FROM table' -d mysql://user:pass@host:3306/db",
        "access": "dbeaver-cli -c 'SELECT * FROM table' -d msaccess:///path/to/db.accdb",
        "dbf": "dbeaver-cli supports DBF via dBase driver",
        "h2": "dbeaver-cli -c 'SELECT * FROM table' -d h2:///path/to/db",
        "firebird": "dbeaver-cli -c 'SELECT * FROM table' -d firebird://host/path/to/db.fdb",
    }
    return hints.get(format, "Refer to DBeaver documentation")


def run_identification(filepath: str) -> dict:
    """Run db_identify.py and parse results."""
    script_dir = Path(__file__).parent
    identify_script = script_dir.parent.parent / "db-identify" / "scripts" / "db_identify.py"
    
    # Try local path first, then assume it's in PATH
    if not identify_script.exists():
        identify_script = "db_identify.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(identify_script), filepath, "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        return {"error": f"Identification failed: {e.stderr}"}
    except json.JSONDecodeError:
        return {"error": "Could not parse identification output"}
    except FileNotFoundError:
        return {"error": "db_identify.py not found - run identification manually"}


def main():
    parser = argparse.ArgumentParser(
        description="Route database to appropriate extraction method",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Route from identification JSON
  python db_route.py --json '{"format": "sqlite", "dbeaver_supported": true}'

  # Route from explicit parameters
  python db_route.py --format berkeleydb --dbeaver-supported false

  # Identify and route in one step
  python db_route.py --file database.db
  
  # Show routing table
  python db_route.py --list-routes
        """
    )
    
    parser.add_argument("--file", "-f", help="Database file (runs identification first)")
    parser.add_argument("--json", "-j", help="Identification JSON from db-identify")
    parser.add_argument("--format", help="Database format")
    parser.add_argument("--dbeaver-supported", type=lambda x: x.lower() == 'true',
                        help="DBeaver CLI support (true/false)")
    parser.add_argument("--confidence", default="high", help="Detection confidence")
    parser.add_argument("--output-json", action="store_true", help="Output as JSON")
    parser.add_argument("--list-routes", "-l", action="store_true", help="List routing table")
    
    args = parser.parse_args()
    
    if args.list_routes:
        print("Database Routing Table:\n")
        print(f"{'Format':<15} {'DBeaver':<10} {'Skill':<25} {'Status':<12}")
        print("-" * 62)
        
        # Get DBeaver support from db-identify if possible
        dbeaver_support = {
            "sqlite": True, "mysql": True, "access": True, "dbf": True,
            "h2": True, "firebird": True, "derby": True,
            "berkeleydb": False, "redis-rdb": False,
        }
        
        for fmt, skill in EXTRACTOR_SKILLS.items():
            dbeaver = "✓" if dbeaver_support.get(fmt) else "✗"
            status = SKILL_STATUS.get(skill, "unknown")
            print(f"{fmt:<15} {dbeaver:<10} {skill:<25} {status:<12}")
        return
    
    # Get identification info
    if args.file:
        id_result = run_identification(args.file)
        if "error" in id_result:
            print(f"ERROR: {id_result['error']}", file=sys.stderr)
            sys.exit(1)
    elif args.json:
        id_result = json.loads(args.json)
    elif args.format:
        id_result = {
            "format": args.format,
            "dbeaver_supported": args.dbeaver_supported,
            "confidence": args.confidence,
        }
    else:
        parser.print_help()
        sys.exit(1)
    
    # Route
    result = route(
        format=id_result.get("format"),
        dbeaver_supported=id_result.get("dbeaver_supported"),
        confidence=id_result.get("confidence", "high"),
    )
    
    # Add source identification
    result["identification"] = id_result
    
    if args.output_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Format: {id_result.get('format', 'unknown')}")
        print(f"Decision: {result['decision']}")
        print(f"Method: {result.get('method', 'none')}")
        print()
        print("Instructions:")
        for instruction in result.get("instructions", []):
            print(f"  • {instruction}")
        
        if result.get("dbeaver_export_hint"):
            print()
            print(f"DBeaver hint: {result['dbeaver_export_hint']}")


if __name__ == "__main__":
    main()
