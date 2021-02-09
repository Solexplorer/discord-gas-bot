# discord-gas-bot
Get the ethereum gas prices in your own discord server.

The gas price reflected here is in Gwei, you can either run it as command with `!gas` or it will show up the price in the sidebar.

## Dependencies
Install all dependencies:
```
pip install -r requirements.txt
```


### Gas Price Bot
1. Copy the [template config](config.yaml.tmpl) and configure with API keys.
```
cp config.yaml.tmpl config.yaml
```
Change config.yaml with the Discord bot key and Etherscan, EthGasStation, or Gasnow API keys.

2. Run a gas price bot using Etherscan API:
```
python gas_bot.py -s ethgasstation
```
Replace `etherscan` with `gasnow` to use Gasnow API (no key required!) or `ethgasstation` to use EthGasStation API.

Ethgasstation is the recommended source
