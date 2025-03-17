from functools import lru_cache
import os
import base58
from solders.keypair import Keypair

# load private key from env
private_key = os.getenv("PRIVATE_KEY")


@lru_cache(maxsize=1)
def get_keypair():
    private_key_bytes = base58.b58decode(private_key)

    # convert private key to keypair
    keypair = Keypair.from_bytes(private_key_bytes)

    return keypair
