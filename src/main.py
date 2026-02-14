import sys

from dotenv import load_dotenv

from .agent import DocAgent
from .config_loader import ConfigLoader
from .llm.claude import ClaudeLLM


# ANSI color codes
class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    # Combinations
    PROMPT = BOLD + CYAN
    USER = "\033[38;5;180m"  # Soft peach/sand - easy on dark mode
    AGENT = WHITE
    HEADER = BOLD + MAGENTA
    INFO = GRAY
    ERROR = "\033[31m"


def main():
    # Load environment variables
    load_dotenv()

    # Initialize components
    try:
        llm = ClaudeLLM()
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure ANTHROPIC_API_KEY is set in .env")
        sys.exit(1)

    config_loader = ConfigLoader()
    agent = DocAgent(llm=llm, config_loader=config_loader)

    # Show available tools
    tools = config_loader.list_tools()
    print(f"{Style.HEADER}DocAgent ready.{Style.RESET}")
    print(f"{Style.INFO}Available tools: {', '.join(tools)}")
    print(f"Commands: exit, quit, reset, tools{Style.RESET}\n")

    # REPL loop
    while True:
        try:
            user_input = input(f"{Style.PROMPT}>>> {Style.RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Style.INFO}Goodbye!{Style.RESET}")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print(f"{Style.INFO}Goodbye!{Style.RESET}")
            break

        if user_input.lower() == "reset":
            agent.reset()
            print(f"{Style.INFO}Conversation history cleared.{Style.RESET}\n")
            continue

        if user_input.lower() == "tools":
            for tool in tools:
                info = config_loader.get_tool_info(tool)
                print(f"  {Style.CYAN}{tool}{Style.RESET}: {info.get('description', '')}")
            print()
            continue

        # Stream the response with visual framing
        print(f"{Style.USER}╭─ DocAgent ───────────────────────────────────────╮{Style.RESET}")
        try:
            print(Style.AGENT, end="")
            for chunk in agent.query(user_input, stream=True):
                print(chunk, end="", flush=True)
            print(f"{Style.RESET}")
            print(f"{Style.USER}╰───────────────────────────────────────────────────╯{Style.RESET}\n")
        except Exception as e:
            print(f"{Style.ERROR}Error: {e}{Style.RESET}\n")


if __name__ == "__main__":
    main()
