"""
Run a Discord bot that takes the !gas command and shows the status in an embed + it shows the prices in the sidebar
"""
# Example:
# python3 gas_run.py -s etherscan &

from typing import Tuple
import logging
import yaml
import discord
import asyncio
from discord.ext.commands import Bot
import argparse


def get_gas_from_etherscan(key: str,
                           verbose: bool = False) -> Tuple[int, int, int]:
    """
    Fetch gas from Etherscan API
    """
    import requests
    import time
    r = requests.get('https://api.etherscan.io/api',
                     params={'module': 'gastracker',
                             'action': 'gasoracle',
                             'apikey': key})
    if r.status_code == 200:
        if verbose:
            print('200 OK')
        data = r.json().get('result')
        return int(data['FastGasPrice']), int(data['ProposeGasPrice']), int(data['SafeGasPrice'])
    else:
        if verbose:
            print(r.status_code)
        time.sleep(10)


def get_gas_from_gasnow(verbose: bool = False) -> Tuple[int, int, int]:
    """
    Fetch gas from Gasnow API
    """
    import requests
    import time
    r = requests.get('https://www.gasnow.org/api/v3/gas/price')
    if r.status_code == 200:
        if verbose:
            print('200 OK')
        data = r.json()['data']
        return int(data['fast'] // 1e9), int(data['standard'] // 1e9), int(data['slow'] // 1e9)
    else:
        if verbose:
            print(r.status_code)
        time.sleep(10)


def get_gas_from_ethgasstation(key: str, verbose: bool = False):
    """
    Fetch gas from ETHGASSTATION API
    """
    import requests
    import time
    r = requests.get('https://ethgasstation.info/api/ethgasAPI.json?', params={'api-key': key})
    if r.status_code == 200:
        if verbose:
            print('200 OK')
        data = r.json()
        return float(data['fastest'] / 10), float(data['fast'] / 10), float(data['average'] / 10), float(
            data['safeLow'] / 10), int(data['fastestWait'] * 60), int(data['fastWait'] * 60), int(
            data['avgWait'] * 60), int(data['safeLowWait'] * 60)
    else:
        if verbose:
            print(r.status_code)
        time.sleep(10)


def main(source, verbose=False):

    # 1. Instantiate the bot 
    bot = Bot(command_prefix="!")

    @bot.command(pass_context=True)
    async def gas(ctx):
        embed = discord.Embed(title=":fuelpump: Current gas prices")
        if source == 'ethgasstation':
            fastest, fast, average, slow, fastestWait, fastWait, avgWait, slowWait = get_gas_from_ethgasstation(
                config['ethgasstationKey'],
                verbose=verbose)
            embed.add_field(name=f"Slow :turtle: | {slowWait} seconds", value=f"{round(float(slow), 1)} Gwei",
                            inline=False)
            embed.add_field(name=f"Average :person_walking: | {avgWait} seconds",
                            value=f"{round(float(average), 1)} Gwei", inline=False)
            embed.add_field(name=f"Fast :race_car: | {fastWait} seconds", value=f"{round(float(fast), 1)} Gwei",
                            inline=False)
            embed.add_field(name=f"Quick :zap: | {fastestWait} seconds", value=f"{round(float(fastest), 1)} Gwei",
                            inline=False)
        else:
            if source == 'etherscan':
                fast, average, slow = get_gas_from_etherscan(config['etherscanKey'], verbose=verbose)
            else:
                fast, average, slow = get_gas_from_gasnow(verbose=verbose)
            embed.add_field(name=f"Slow   :turtle:", value=f"{slow} Gwei", inline=False)
            embed.add_field(name=f"Average   :person_walking:", value=f"{average} Gwei", inline=False)
            embed.add_field(name=f"Fast   :zap:", value=f"{fast} Gwei", inline=False)
        await ctx.send(embed=embed)

    # 2. Load config
    filename = 'config.yaml'
    with open(filename) as f:
        config = yaml.load(f, Loader=yaml.Loader)

    async def send_update(fastest, average, slow, **kw):
        status = f'⚡{fastest} | 🚶{average} | 🐢{slow}'
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                            name=status))
        await asyncio.sleep(config['updateFreq'])  # in seconds

    @bot.event
    async def on_message(message):
        # do some extra stuff here
        await bot.process_commands(message)

    @bot.event
    async def on_ready():
        """
        When discord client is ready
        """
        while True:
            # 3. Fetch gas
            if source == 'etherscan':
                gweiList = get_gas_from_etherscan(config['etherscanKey'],
                                                  verbose=verbose)
            elif source == 'gasnow':
                gweiList = get_gas_from_gasnow(verbose=verbose)
            elif source == 'ethgasstation':
                gweiList = get_gas_from_ethgasstation(config['ethgasstationKey'])
                await send_update(gweiList[0], gweiList[2], gweiList[3])
                continue
            else:
                raise NotImplemented('Unsupported source')
            # 4. Feed it to the bot
            await send_update(*gweiList)

    bot.run(config['discordBotKey'])


if __name__ == '__main__':
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    parser = argparse.ArgumentParser()

    parser.add_argument('-s', '--source',
                        choices=['etherscan', 'gasnow', 'ethgasstation'],
                        default='etherscan',
                        help='select API')

    parser.add_argument('-v', '--verbose',
                        action='store_true',  # equiv. default is False
                        help='toggle verbose')
    args = parser.parse_args()
    main(source=args.source,
         verbose=args.verbose)
