# discord-gas-bot
Get the ethereum gas prices in your own discord server.

The gas price reflected here is in Gwei, you can either run it as command with `!gas` or it will show up the price in the sidebar.

## Dependencies
Install all dependencies:
```
pip install -r requirements.txt
```


### Gas Price Bot
1. Configure [config.yaml](config.yaml) using the template provided.
It requires a unique Discord bot key.
It also requires an Etherscan API key if you would like to use Etherscan API or an EthGasStation API if you wish to use EthGasStation.

2. Run a gas price bot using Etherscan API:
```
python gas_run.py -s etherscan
```
Replace `etherscan` with `gasnow` to use Gasnow API (no key required!) or `ethgasstation` to use EthGasStation API.


