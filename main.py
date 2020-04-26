import os

from dotenv import load_dotenv

from discord_bot_cud.bot import main

if __name__ == "__main__":
    load_dotenv()
    main(token=os.getenv('DISCORD_TOKEN'))
