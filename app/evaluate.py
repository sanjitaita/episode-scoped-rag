import argparse
import json
import time
from pathlib import Path

from app.answer import NOT_COVERED, answer
from app.llm import CHAT_MODEL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVALS_DIR = PROJECT_ROOT / "evals"


def load_cases() -> list[dict]:
    cases = []
    for path in sorted(EVALS_DIR.glob("*.json")):
        cases.extend(json.loads(path.read_text(encoding="utf-8")))
    return cases


def check(case: dict, result: dict) -> list[str]:
    failures = []
    reply = result["answer"].replace("’", "'").strip()
    text = reply.lower()
    watched = (case["season"], case["episode"])

    for source in result["sources"]:
        if (source["season"], source["episode"]) > watched:
            failures.append(f"spoiler: S{source['season']}E{source['episode']} is past the watch point")

    if case["refuse"]:
        if reply != NOT_COVERED:
            failures.append("should have refused")
        return failures

    retrieved = []
    for source in result["sources"]:
        retrieved.append((source["season"], source["episode"]))

    for season, episode in case["expected_sources"]:
        if (season, episode) not in retrieved:
            failures.append(f"retrieval: S{season}E{episode} not in sources")

    for group in case["must_include"]:
        found = False
        for word in group:
            if word.lower() in text:
                found = True
                break
        if not found:
            failures.append(f"missing one of {group}")

    for phrase in case["must_not_include"]:
        if phrase.lower() in text:
            failures.append(f"contains '{phrase}'")

    return failures


def run_case(case: dict, mode: str, runs: int) -> int:
    passed = 0
    notes = []
    for run in range(1, runs + 1):
        result = answer(case["question"], case["show"], case["season"], case["episode"], mode=mode)
        failures = check(case, result)
        if failures:
            notes.append(f"    run {run}: {'; '.join(failures)}")
            notes.append(f"    answer: {result['answer']}")
        else:
            passed += 1

    print(f"{case['id']:<22} {mode:<6} {passed}/{runs}")
    for note in notes:
        print(note)
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the eval cases and score the answers.")
    parser.add_argument("--runs", type=int, default=3, help="How many times to ask each question.")
    parser.add_argument("--only", type=str, help="Run one case by its id.")
    parser.add_argument("--show", type=str, help="Run only the cases for one show.")
    args = parser.parse_args()

    cases = load_cases()
    if args.only:
        selected = []
        for case in cases:
            if case["id"] == args.only:
                selected.append(case)
        if not selected:
            parser.error(f"No case with id '{args.only}'")
        cases = selected

    if args.show:
        selected = []
        for case in cases:
            if case["show"] == args.show:
                selected.append(case)
        if not selected:
            parser.error(f"No cases for show '{args.show}'")
        cases = selected

    print(f"Model: {CHAT_MODEL}   runs per question: {args.runs}\n")
    start = time.time()
    total_passed = 0
    total_runs = 0

    try:
        for case in cases:
            for mode in case["modes"]:
                total_passed += run_case(case, mode, args.runs)
                total_runs += args.runs
    except ConnectionError:
        parser.exit(1, "Could not reach Ollama. Start it and try again.\n")

    minutes = (time.time() - start) / 60
    print(f"\nTotal: {total_passed}/{total_runs} passed in {minutes:.1f} min")


if __name__ == "__main__":
    main()