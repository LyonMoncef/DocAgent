import argparse
import json
import sys
import threading
import time

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


class Spinner:
    """Animated spinner for loading states."""

    def __init__(self, message: str = "Processing"):
        self.message = message
        self.running = False
        self.thread = None
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def _spin(self):
        i = 0
        while self.running:
            frame = self.frames[i % len(self.frames)]
            print(f"\r{Style.INFO}{frame} {self.message}...{Style.RESET}", end="", flush=True)
            time.sleep(0.1)
            i += 1

    def start(self, message: str = None):
        if message:
            self.message = message
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        print("\r" + " " * 50 + "\r", end="", flush=True)  # Clear line

    def update(self, message: str):
        self.message = message


def _parse_args():
    parser = argparse.ArgumentParser(description="DocAgent — dotfiles/config management assistant")
    parser.add_argument("--export", metavar="TOOL", help="Export widget data for a tool (no LLM needed)")
    parser.add_argument("--widget-type", default="shortcut_table", help="Widget type to export (default: shortcut_table)")
    parser.add_argument("-o", "--output", metavar="FILE", help="Output file path (default: stdout)")
    return parser.parse_args()


def _run_export(args):
    """Run export mode — no LLM required."""
    config_loader = ConfigLoader()
    # Create agent with a dummy LLM (not used in export)
    agent = DocAgent(llm=None, config_loader=config_loader)
    result = agent._tool_export_widget_data(args.export, args.widget_type)

    # Check if the result is valid JSON (success) or an error message
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        print(f"Error: {result}", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(data, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output + "\n")
        print(f"Exported to {args.output}", file=sys.stderr)
    else:
        print(output)


def main():
    args = _parse_args()

    # Export mode — no LLM needed
    if args.export:
        _run_export(args)
        return

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

        # Process query with visual feedback
        spinner = Spinner("Loading configs")
        spinner.start()

        print(f"{Style.USER}╭─ DocAgent ───────────────────────────────────────╮{Style.RESET}")
        try:
            first_chunk = True
            for chunk in agent.query(user_input, stream=True):
                if first_chunk:
                    spinner.stop()
                    print(Style.AGENT, end="")
                    first_chunk = False

                # Tool execution feedback
                if chunk.startswith("[Tool:"):
                    print(f"{Style.GREEN}{chunk}{Style.RESET}", end="", flush=True)
                    spinner.start("Waiting for response")
                else:
                    spinner.stop()
                    print(chunk, end="", flush=True)

            spinner.stop()
            print(f"{Style.RESET}")
            print(f"{Style.USER}╰───────────────────────────────────────────────────╯{Style.RESET}\n")
        except Exception as e:
            spinner.stop()
            print(f"\n{Style.ERROR}Error: {e}{Style.RESET}")
            print(f"{Style.USER}╰───────────────────────────────────────────────────╯{Style.RESET}\n")


if __name__ == "__main__":
    main()
