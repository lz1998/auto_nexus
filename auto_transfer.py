import os
import tqdm

MAIN_PRIVATE_KEY = os.environ["MAIN_PRIVATE_KEY"]


address_list = os.listdir("accounts")
for address in tqdm.tqdm(address_list):
    try:
        address = address.split(".")[0]
        os.environ["TO_WALLET_ADDRESS"] = address
        os.system("node transfer.js")
    except Exception as e:
        print(e)
