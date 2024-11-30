import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound
import json


private_key = f"your_cay" # приватный ключ

resepient = f"your_resepient" # адрес получателя

w3_async = AsyncWeb3(AsyncHTTPProvider('https://arbitrum.rpc.subquery.network/public'))  # укажите рпс нужной сети
getadres =  w3_async.eth.account.from_key(private_key).address


value = 2  # количество токенов для перевода

balance_wallet = []
explorer_url = 'https://arbiscan.io/' # ссылка на эксплоер нужной сети для получения ссылки на транзу

what_gas = 50   #Максимальный газ в эфире

contract_address = f"0xaf88d065e77c8cC2239327C5EDb3A432268e5831"  # ардрес контракта в вашей сети


async def load_abi(filename):
    with open(filename, 'r') as abi_file:
        abi = json.load(abi_file)
    return abi

a = asyncio.run(load_abi("abi.json"))

contract = w3_async.eth.contract(address=contract_address, abi=a)


async def wait_gas():
    w3_async_eth = AsyncWeb3(AsyncHTTPProvider('https://eth.meowrpc.com'))
    gas = await w3_async_eth.eth.gas_price
    gas = w3_async_eth.from_wei(gas, 'gwei')
    print(f"Текущий газ {gas}")
    print()
    while gas > what_gas:
        print(f"Текущий газ {gas}, ожидаю снижение")
        await asyncio.sleep(20)
        if gas < what_gas:
            break



async def get_balance(main_key):
    try:
        address = f"{main_key}"
        checksum_address = w3_async.to_checksum_address(address)
        balance = await w3_async.eth.get_balance(checksum_address)
        ether_balance = w3_async.from_wei(balance, 'ether')
        balance_wallet.append(ether_balance)
        print(f"Баланс кошелька {checksum_address}: {ether_balance} ETH")
        # ПОЛУЧЕАМ ИНФОРМАЦИЮ О БАЛАНСЕ ТОКЕНА ЕРС20

        balance_contract = await contract.functions.balanceOf(main_key).call()
        decimals = await contract.functions.decimals().call()
        readable_value = balance_contract / (10 ** decimals)

        print(f"Баланс {await contract.functions.symbol().call()}: {readable_value}")
        print()
        if  w3_async.from_wei(balance_contract, 'mwei') < value:
            print(f"Недостаточный баланс {await contract.functions.symbol().call()} для перевода")
            print(f"Требуется пополнить баланс на {(readable_value-value)*-1} {await contract.functions.symbol().call()}")
            exit()
    except ValueError:
        if main_key==getadres:
            print("Вы ввели не верный адрес кошелька, попробуйте снова")
            exit()
        if main_key == resepient:print("Вы ввели не верный адрес получателя, попробуйте снова")
        exit()


async def get_gas():
    await wait_gas()
    await get_balance(getadres)
    await get_balance(resepient)
    base_fee = await w3_async.eth.gas_price
    max_priority_fee_per_gas = await w3_async.eth.max_priority_fee

    if max_priority_fee_per_gas == 0:
        max_priority_fee_per_gas = base_fee

    max_fee_per_gas = int(base_fee * 1.25 + max_priority_fee_per_gas)
    max_fee_per_gas_eth = w3_async.from_wei(max_fee_per_gas, 'ether')
    if (w3_async.to_wei(balance_wallet[0], 'ether')-max_fee_per_gas_eth) <= 0:
        print("Недостаточно газа для создания транзации")
        exit()


async def wait_tx(tx_hash):
    total_time = 0
    timeout = 120
    poll_latency = 10
    while True:
        try:
            receipts = await w3_async.eth.get_transaction_receipt(tx_hash)
            status = receipts.get("status")
            if status == 1:
                print(f'Transaction was successful: {explorer_url}tx/{tx_hash.hex()}')
                return True
            elif status is None:
                await asyncio.sleep(poll_latency)
            else:
                print(f'Transaction failed: {explorer_url}tx/{tx_hash.hex()}')
                return False
        except TransactionNotFound:
            if total_time > timeout:
                print(f"Transaction is not in the chain after {timeout} seconds")
                return False
            total_time += poll_latency
            await asyncio.sleep(poll_latency)

async def main():
    await get_gas()
    try:
        tx = await contract.functions.transfer(resepient, w3_async.to_wei(value, "mwei")).build_transaction({
            'from': w3_async.to_checksum_address(getadres),
            'nonce': await w3_async.eth.get_transaction_count(getadres),
            'maxPriorityFeePerGas': await w3_async.eth.max_priority_fee,
            'maxFeePerGas': int(await w3_async.eth.gas_price * 1.25 + await w3_async.eth.max_priority_fee),
            'chainId': await w3_async.eth.chain_id
        })
        tx['gas'] = int((await w3_async.eth.estimate_gas(tx)) * 1.5)
        signed_tx = w3_async.eth.account.sign_transaction(tx, private_key)
        tx_hash = await w3_async.eth.send_raw_transaction(signed_tx.rawTransaction)


      #  transaction['gas'] = int((await w3_async.eth.estimate_gas(transaction)) * 1.5)

      #  tx_hash = await sign_and_send_tx(transaction)
        print("Выполняю перевод токенов")
        await wait_tx(tx_hash)
    except ValueError:
        print(f"На счету нет суммы {value} для перевода, проверьте баланс или сумму перевода")
        exit()


async def info_after_transfer(main_key):
    address = f"{main_key}"
    checksum_address = w3_async.to_checksum_address(address)
    balance = await w3_async.eth.get_balance(checksum_address)
    ether_balance = w3_async.from_wei(balance, 'ether')
    balance_contract = await contract.functions.balanceOf(main_key).call()
    decimals = await contract.functions.decimals().call()
    readable_value = balance_contract / (10 ** decimals)
    print(f"Баланс кошелька {checksum_address} после трансфера: {ether_balance} ETH")
    balance_contract = await contract.functions.balanceOf(main_key).call()
    print(f"Баланс {await contract.functions.symbol().call()}: {readable_value}")
    print()

async def transfer():
    await main()
    await info_after_transfer(getadres)
    await info_after_transfer(resepient)

asyncio.run(transfer())


