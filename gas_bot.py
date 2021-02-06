"""
Run a Discord bot that takes the !gas command and shows the status in an embed + shows the prices in the sidebar
"""
# Example:
# python3 gas_bot.py -s etherscan

from typing import Tuple
import logging
import yaml
import discord
import asyncio
from discord.ext.commands import Bot
import argparse
import requests
import time


def get_gas_from_etherscan(key: str,
                           verbose: bool = False) -> Tuple[int, int, int]:
    """
    Fetch gas from Etherscan API
    """
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
    r = requests.get('https://ethgasstation.info/api/ethgasAPI.json?', params={'api-key': key})
    if r.status_code == 200:
        if verbose:
            print('200 OK')
        data = r.json()
        return int(data['fastest'] / 10), int(data['fast'] / 10), int(data['average'] / 10), int(
            data['safeLow'] / 10), int(data['fastestWait'] * 60), int(data['fastWait'] * 60), int(
            data['avgWait'] * 60), int(data['safeLowWait'] * 60)
    else:
        if verbose:
            print(r.status_code)
        time.sleep(10)


def main(source, verbose=False):
    # 1. Instantiate the bot
    bot = Bot(command_prefix="!", help_command=None)

    @bot.command(pass_context=True, brief="Get ETH gas prices")
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
            embed.add_field(name=f"Slow :turtle:", value=f"{slow} Gwei", inline=False)
            embed.add_field(name=f"Average :person_walking:", value=f"{average} Gwei", inline=False)
            embed.add_field(name=f"Fast :zap:", value=f"{fast} Gwei", inline=False)
        embed.set_footer(text=f"Fetched from {source}\nUse help to get the list of commands")
        embed.set_author(
            name='{0.display_name}'.format(ctx.author),
            icon_url='{0.avatar_url}'.format(ctx.author)
        )
        await ctx.send(embed=embed)

    @bot.command(pass_context=True, brief="Get the cost for each tx type")
    async def fees(ctx):
        calculate_eth_tx = lambda gwei, limit: round(gwei * limit * 0.000000001, 4)
        fast = get_gas_from_gasnow(verbose=verbose)[0]
        eth_price = \
            requests.get('https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd').json()[
                'ethereum'][
                'usd']
        simple_tx_fee_eth = calculate_eth_tx(fast, 21000)
        simple_tx_fee_usd = round(simple_tx_fee_eth * eth_price, 2)
        token_approve_eth = calculate_eth_tx(fast, 51000)
        token_approve_usd = round(token_approve_eth * eth_price, 2)
        token_transfer_eth = calculate_eth_tx(fast, 48000)
        token_transfer_usd = round(token_transfer_eth * eth_price, 2)
        range1_uniswap_eth = calculate_eth_tx(fast, 120000)
        range1_uniswap_usd = round(range1_uniswap_eth * eth_price, 2)
        range2_uniswap_eth = calculate_eth_tx(fast, 200000)
        range2_uniswap_usd = round(range2_uniswap_eth * eth_price, 2)
        fees_eth = f"Simple ETH TX: **{simple_tx_fee_usd}$** ({simple_tx_fee_eth} Ξ)\n" \
                   f"Token Approval (ERC20): **{token_approve_usd}$** ({token_approve_eth} Ξ)\n" \
                   f"Token Transfer (ERC20): **{token_transfer_usd}$** ({token_transfer_eth} Ξ)\n" \
                   f"Uniswap Trades: **${range1_uniswap_usd} - ${range2_uniswap_usd}** ({range1_uniswap_eth} Ξ - {range2_uniswap_eth} Ξ)\n"

        await ctx.send(fees_eth)

    @bot.command(pass_context=True, brief="Get list of commands")
    async def help(ctx, args=None):
        help_embed = discord.Embed(
            title="Gas Tracker",
            colour=discord.Colour.from_rgb(206, 17, 38))
        help_embed.set_author(
            name='{0.display_name}'.format(ctx.author),
            icon_url='{0.avatar_url}'.format(ctx.author)
        )
        command_list = [x for x in bot.commands if not x.hidden]

        def sortCommands(value):
            return value.name

        command_list.sort(key=sortCommands)
        if not args:
            help_embed.add_field(
                name="Command Prefix",
                value="`!`",
                inline=False)
            help_embed.add_field(
                name="List of supported commands:",
                value="```" + "\n".join(['{:>2}. {:<14}{}'.format(str(i + 1), x.name, x.brief) for i, x in
                                         enumerate(command_list)]) + "```",
                inline=False
            )
        else:
            help_embed.add_field(
                name="Nope.",
                value="Don't think I got that command, boss."
            )

        help_embed.set_footer(text="For any inquiries, suggestions, or bug reports, get in touch with @Nerte#1804")
        await ctx.send(embed=help_embed)

    # 2. Load config
    filename = 'config.yaml'
    with open(filename) as f:
        config = yaml.load(f, Loader=yaml.Loader)

    async def send_update(fastest, average, slow, **kw):
        status = f'⚡{fastest} | 🚶{average} | 🐢{slow} | !help'
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,
                                                            name=status))
        await asyncio.sleep(config['updateFreq'])  # in seconds

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
                        action='store_true',
                        help='toggle verbose')
    args = parser.parse_args()
    main(source=args.source,
         verbose=args.verbose)
