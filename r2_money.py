from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from eth_account.messages import encode_defunct
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime, timezone
from colorama import *
import asyncio, random, json, time, re, os, pytz
from eth_utils import to_hex

wib = pytz.timezone('Asia/Jakarta')

class R2Money:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://www.r2.money",
            "Referer": "https://www.r2.money/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.BASE_API = "https://www.r2.money"
        self.RPC_URL = "https://api.zan.top/node/v1/pharos/testnet/54b49326c9f44b6e8730dc5dd4348421"
        self.CHAIN_ID = 688688
        self.APPROVAL_CONTRACT1 = "0x8bebfcbe5468f146533c182df3dfbf5ff9be00e2"
        self.SWAP_CONTRACT = "0x4f5b54d4AF2568cefafA73bB062e5d734b55AA05"
        self.APPROVAL_CONTRACT2 = "0x4f5b54d4af2568cefafa73bb062e5d734b55aa05"
        self.EARN_CONTRACT = "0xf8694d25947a0097cb2cea2fc07b071bdf72e1f8"
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.used_nonce = {}
        self.min_delay = 0
        self.max_delay = 0
        self.swap_amount = 0
        self.earn_times = 0
        self.earn_amount_min = 0.1  # Minimum earn amount (fixed at 0.1)
        self.earn_amount_max = 0
        self.earn_delay_min = 0
        self.earn_delay_max = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "\n" + "═" * 60)
        print(Fore.GREEN + Style.BRIGHT + "    ⚡ R2 Money Automation BOT ⚡")
        print(Fore.CYAN + Style.BRIGHT + "    ────────────────────────────────")
        print(Fore.YELLOW + Style.BRIGHT + "    🧠 Project    : R2 Money - Automation Bot")
        print(Fore.YELLOW + Style.BRIGHT + "    🧑‍💻 Author     : Assistant")
        print(Fore.YELLOW + Style.BRIGHT + "    🌐 Status     : Running & Monitoring...")
        print(Fore.CYAN + Style.BRIGHT + "    ────────────────────────────────")
        print(Fore.MAGENTA + Style.BRIGHT + "    🧬 Powered by AI | v1.0 🚀")
        print(Fore.LIGHTGREEN_EX + Style.BRIGHT + "═" * 60 + "\n")

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")

    def generate_address(self, private_key: str):
        try:
            account = Account.from_key(private_key)
            return account.address
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Generate Address Failed: {str(e)}{Style.RESET_ALL}")
            return None

    def authenticate_wallet(self, private_key: str):
        """Authenticate wallet by signing the r2.money login message with dynamic nonce"""
        try:
            # Generate dynamic nonce based on current timestamp
            nonce = str(int(time.time()))
            message = f"Welcome! Sign this message to login to r2.money. This doesn't cost you anything and is free of any gas fees. Nonce: {nonce}"
            
            # Sign the message with the wallet
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=private_key)
            signature = to_hex(signed_message.signature)
            
            self.log(f"{Fore.GREEN + Style.BRIGHT}Wallet Authentication: {Style.RESET_ALL}")
            self.log(f"{Fore.CYAN + Style.BRIGHT}  Message: {Style.RESET_ALL}{message}")
            self.log(f"{Fore.CYAN + Style.BRIGHT}  Signature: {Style.RESET_ALL}{signature}")
            self.log(f"{Fore.GREEN + Style.BRIGHT}✅ Wallet authenticated successfully{Style.RESET_ALL}")
            
            return True
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}❌ Wallet Authentication Failed: {str(e)}{Style.RESET_ALL}")
            return False

    async def get_web3(self, use_proxy: bool, address: str):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        request_kwargs = {}
        if proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}
        return Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))

    async def perform_approval1(self, private_key: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3(use_proxy, address)
            nonce = web3.eth.get_transaction_count(address)
            tx = {
                'to': web3.to_checksum_address(self.APPROVAL_CONTRACT1),
                'value': 0,
                'gas': 200000,
                'gasPrice': web3.to_wei('20', 'gwei'),
                'nonce': nonce,
                'chainId': self.CHAIN_ID,
                'data': '0x095ea7b30000000000000000000000004f5b54d4af2568cefafa73bb062e5d734b55aa05ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
            }
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            self.log(f"{Fore.GREEN + Style.BRIGHT}✅ Approval 1 successful: {web3.to_hex(tx_hash)}{Style.RESET_ALL}")
            return web3.to_hex(tx_hash)
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}❌ Approval 1 failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def perform_swap(self, private_key: str, address: str, amount: int, use_proxy: bool):
        try:
            web3 = await self.get_web3(use_proxy, address)
            nonce = web3.eth.get_transaction_count(address)
            tx = {
                'chainId': self.CHAIN_ID,
                'from': web3.to_checksum_address(address),
                'to': web3.to_checksum_address(self.SWAP_CONTRACT),
                'gas': int('0x20e9e', 16),
                'gasPrice': int('0x4a817c80', 16),
                'nonce': nonce,
                'value': 0,
                'data': f'0x095e7a95000000000000000000000000{address[2:].lower()}00000000000000000000000000000000000000000000000000000000{hex(amount)[2:].zfill(8)}0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
            }
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            self.log(f"{Fore.GREEN + Style.BRIGHT}✅ Swap successful: {web3.to_hex(tx_hash)}{Style.RESET_ALL}")
            return web3.to_hex(tx_hash)
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}❌ Swap failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def perform_approval2(self, private_key: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3(use_proxy, address)
            nonce = web3.eth.get_transaction_count(address)
            tx = {
                'to': web3.to_checksum_address(self.APPROVAL_CONTRACT2),
                'value': 0,
                'gas': 200000,
                'gasPrice': web3.to_wei('20', 'gwei'),
                'nonce': nonce,
                'chainId': self.CHAIN_ID,
                'data': '0x095ea7b3000000000000000000000000f8694d25947a0097cb2cea2fc07b071bdf72e1f8ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
            }
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            self.log(f"{Fore.GREEN + Style.BRIGHT}✅ Approval 2 successful: {web3.to_hex(tx_hash)}{Style.RESET_ALL}")
            return web3.to_hex(tx_hash)
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}❌ Approval 2 failed: {str(e)}{Style.RESET_ALL}")
            return None

    async def perform_add_earn(self, private_key: str, address: str, amount: int, use_proxy: bool):
        try:
            web3 = await self.get_web3(use_proxy, address)
            nonce = web3.eth.get_transaction_count(address)
            tx = {
                'to': web3.to_checksum_address(self.EARN_CONTRACT),
                'value': 0,
                'gas': 200000,
                'gasPrice': web3.to_wei('20', 'gwei'),
                'nonce': nonce,
                'chainId': self.CHAIN_ID,
                'data': f'0x1a5f0f00{hex(amount)[2:].zfill(64)}0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
            }
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            self.log(f"{Fore.GREEN + Style.BRIGHT}✅ Add to earn successful: {web3.to_hex(tx_hash)}{Style.RESET_ALL}")
            return web3.to_hex(tx_hash)
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}❌ Add to earn failed: {str(e)}{Style.RESET_ALL}")
            return None

    def print_question(self):
        while True:
            try:
                self.swap_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter swap amount: {Style.RESET_ALL}").strip())
                break
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                self.earn_times = int(input(f"{Fore.YELLOW + Style.BRIGHT}Number of times to add to earn: {Style.RESET_ALL}").strip())
                break
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        print(f"{Fore.CYAN + Style.BRIGHT}📊 Earn Amount Configuration:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW + Style.BRIGHT}  • Minimum earn amount: 0.1 (fixed){Style.RESET_ALL}")
        while True:
            try:
                self.earn_amount_max = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter maximum earn amount (must be >= 0.1): {Style.RESET_ALL}").strip())
                if self.earn_amount_max >= 0.1:
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Maximum amount must be >= 0.1{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                self.earn_delay_min = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min delay for earn (seconds): {Style.RESET_ALL}").strip())
                self.earn_delay_max = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max delay for earn (seconds): {Style.RESET_ALL}").strip())
                break
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter numbers.{Style.RESET_ALL}")

        while True:
            try:
                use_proxy_choice = int(input(f"{Fore.YELLOW + Style.BRIGHT}Use proxy? 1 for yes, 0 for no: {Style.RESET_ALL}").strip())
                break
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input.{Style.RESET_ALL}")

        return use_proxy_choice

    async def process_account(self, private_key: str, use_proxy: bool):
        address = self.generate_address(private_key)
        if not address:
            return

        self.log(f"{Fore.MAGENTA + Style.BRIGHT}🚀 Processing address: {address}{Style.RESET_ALL}")

        # Step 1: Authenticate wallet with signature (one time login)
        self.log(f"{Fore.YELLOW + Style.BRIGHT}📝 Step 1: Wallet Authentication{Style.RESET_ALL}")
        auth_success = self.authenticate_wallet(private_key)
        if not auth_success:
            self.log(f"{Fore.RED + Style.BRIGHT}❌ Authentication failed for {address}{Style.RESET_ALL}")
            return

        # Step 2: First approval (one time)
        self.log(f"{Fore.YELLOW + Style.BRIGHT}📝 Step 2: First Approval (0x8bebfcbe...){Style.RESET_ALL}")
        await self.perform_approval1(private_key, address, use_proxy)

        # Step 3: Swap (user defined amount)
        self.log(f"{Fore.YELLOW + Style.BRIGHT}📝 Step 3: Performing Swap{Style.RESET_ALL}")
        swap_amount_wei = int(self.swap_amount * 10**6)  # USDC has 6 decimals
        self.log(f"{Fore.CYAN + Style.BRIGHT}  Swapping {self.swap_amount} USDC (Wei: {swap_amount_wei}){Style.RESET_ALL}")
        await self.perform_swap(private_key, address, swap_amount_wei, use_proxy)

        # Step 4: Second approval (one time, unlimited)
        self.log(f"{Fore.YELLOW + Style.BRIGHT}📝 Step 4: Second Approval (0x4f5b54d4...){Style.RESET_ALL}")
        await self.perform_approval2(private_key, address, use_proxy)

        # Step 5: Add to earn (multiple times with delay and random amounts)
        self.log(f"{Fore.YELLOW + Style.BRIGHT}📝 Step 5: Adding to Earn ({self.earn_times} times){Style.RESET_ALL}")
        self.log(f"{Fore.CYAN + Style.BRIGHT}  📊 Amount Range: {self.earn_amount_min} - {self.earn_amount_max} tokens{Style.RESET_ALL}")
        
        for i in range(self.earn_times):
            # Generate random amount between min and max
            random_earn_amount = round(random.uniform(self.earn_amount_min, self.earn_amount_max), 3)
            earn_amount_hex = int(random_earn_amount * 10**6)  # Convert to proper decimals (assuming 6 decimals)
            
            self.log(f"{Fore.CYAN + Style.BRIGHT}  💰 Earn transaction {i+1}/{self.earn_times}{Style.RESET_ALL}")
            self.log(f"{Fore.GREEN + Style.BRIGHT}  🎲 Random amount: {random_earn_amount} tokens (Wei: {earn_amount_hex}){Style.RESET_ALL}")
            
            await self.perform_add_earn(private_key, address, earn_amount_hex, use_proxy)
            
            if i < self.earn_times - 1:  # Don't delay after last transaction
                delay = random.randint(self.earn_delay_min, self.earn_delay_max)
                self.log(f"{Fore.BLUE + Style.BRIGHT}  ⏳ Waiting {delay} seconds...{Style.RESET_ALL}")
                await asyncio.sleep(delay)

        self.log(f"{Fore.GREEN + Style.BRIGHT}✅ All tasks completed for {address}{Style.RESET_ALL}")

    async def main(self):
        self.clear_terminal()
        self.welcome()

        with open('accounts.txt', 'r') as f:
            private_keys = [line.strip() for line in f if line.strip()]

        self.log(f"Total accounts: {len(private_keys)}")

        use_proxy = self.print_question()

        if use_proxy:
            await self.load_proxies(2)  # Assuming private proxies

        tasks = []
        for pk in private_keys:
            tasks.append(self.process_account(pk, use_proxy))

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    bot = R2Money()
    asyncio.run(bot.main())
