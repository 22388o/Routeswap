from os.path import expanduser, isfile
from os import environ, makedirs

import codecs

makedirs("./data", exist_ok=True)

# API configuration.
API_HOST = environ.get("API_HOST", "0.0.0.0")
API_PORT = environ.get("API_PORT", 1536)

# Redis configuration.
REDIS_HOST = environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = environ.get("REDIS_PORT", 6379)
REDIS_PASS = environ.get("REDIS_PASS", "")

# Currencies configuration.
SUPPORTED_CURRENCIES = environ.get("SUPPORTED_CURRENCIES", "LN-BTC,BTC").split(",")

# Loop configuration.
LOOP_MIN_BTC = float(environ.get("LOOP_MIN_BTC", 0.00010000))
LOOP_IN_ACTIVE = environ.get("LOOP_IN_ACTIVE", True)
if (LOOP_IN_ACTIVE == "true") or (LOOP_IN_ACTIVE == True):
    LOOP_IN_ACTIVE = True
else:
    LOOP_IN_ACTIVE = False

LOOP_OUT_ACTIVE = environ.get("LOOP_OUT_ACTIVE", True)
if (LOOP_OUT_ACTIVE == "true") or (LOOP_OUT_ACTIVE == True):
    LOOP_OUT_ACTIVE = True
else:
    LOOP_OUT_ACTIVE = False

SERVICE_FEE_RATE = float(environ.get("SERVICE_FEE_RATE", 1))
SERVICE_MIN_FEE_RATE = float(environ.get("SERVICE_MIN_FEE_RATE", 0.00000500))

# Bitcoin configuration.
BTC_HOST = environ.get("BTC_HOST")
BTC_USER = environ.get("BTC_USER")
BTC_PASS = environ.get("BTC_PASS")

LN_BACKEND = "lnd"

# Lnd configuration.
LND_PATH = expanduser("~/.lnd")
LND_HOST = environ.get("LND_HOST", "https://127.0.0.1:8080")
LND_MACAROON = environ.get("LND_MACAROON")
if (LND_MACAROON == None):
    if isfile(LND_PATH + "/data/chain/bitcoin/mainnet/admin.macaroon"):
        with open(LND_PATH + "/data/chain/bitcoin/mainnet/admin.macaroon", "rb") as r:
            LND_MACAROON = codecs.encode(r.read(), "hex")

LND_CERTIFICATE = environ.get("LND_CERTIFICATE", LND_PATH + "/tls.cert")
LND_MAX_FEERATE = float(environ.get("LND_MAX_FEERATE", 1))
