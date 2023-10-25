import asyncio

from src.cli import cli

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cli())
