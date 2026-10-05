import argparse

from app.answer import answer
from app.retrieval import SpoilerFilterError


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a spoiler-safe question about a show."
    )
    parser.add_argument("--question", type=str, help="The question to ask.", required=True)
    parser.add_argument("--show", type=str, help="The name of the show.", required=True)
    parser.add_argument("--season", type=int, help="The season number.", required=True)
    parser.add_argument("--episode", type=int, help="The episode number.", required=True)

    args = parser.parse_args()

    try:
        result = answer(args.question, args.show, args.season, args.episode)
    except ValueError as error:
        parser.error(str(error))
    except SpoilerFilterError as error:
        parser.exit(1, f"{error}\n")
    except ConnectionError:
        parser.exit(
            1,
            "Could not reach Ollama. Start it with 'ollama serve' and try again.\n",
        )

    print(result["answer"])

    if result["sources"]:
        print("\nSources:")
        for source in result["sources"]:
            print(f"  S{source['season']}E{source['episode']} {source['title']}")


if __name__ == "__main__":
    main()