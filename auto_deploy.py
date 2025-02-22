import os
import tqdm

MAIN_PRIVATE_KEY = os.environ["MAIN_PRIVATE_KEY"]


address_list = os.listdir("accounts")
for address in tqdm.tqdm(address_list):
    try:
        address = address.split(".")[0]
        with open(f"accounts/{address}.txt", "r") as f:
            private_key = f.read()
        os.environ["PRIVATE_KEY"] = private_key
        os.system("node deploy.js")
    except Exception as e:
        print(e)
