#!/usr/bin/env bash

set -e

mkdir -p abi

jq '.abi' \
  out/CarbonProjectNFT.sol/CarbonProjectNFT.json \
  > abi/CarbonProjectNFT.json

jq '.abi' \
  out/CarbonCredit.sol/CarbonCredit.json \
  > abi/CarbonCredit.json

echo "ABI exported."