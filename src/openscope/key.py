#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/28 13:55
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : key..py
# @Software: PyCharm
# @Desc    :
# @Cmd     :
from typing import Dict, List, Tuple, Union

import sr25519  # type: ignore
from substrateinterface import Keypair, KeypairType  # type: ignore
from substrateinterface.utils import ss58  # type: ignore


def is_ss58_address(address: str, ss58_format: int = 42) -> bool:
    """
    Validates whether the given string is a valid SS58 address.

    Args:
        address: The string to validate.
        ss58_format: The SS58 format code to validate against.

    Returns:
        True if the address is valid, False otherwise.
    """

    return ss58.is_valid_ss58_address(address, valid_ss58_format=ss58_format)


def generate_keypair(mnemonic: str = None, private_key: str = None) -> Keypair:
    """
    Generates a new keypair.
    """
    if private_key:
        keypair = Keypair.create_from_private_key(bytes.fromhex(private_key), ss58_format=42)
    else:
        mnemonic = mnemonic or Keypair.generate_mnemonic()
        keypair = Keypair.create_from_mnemonic(mnemonic)
    return keypair


def _format_data(data: Union[List, Dict, Tuple, str]) -> bytes:
    '''
    format data to str message
    :param data:
    :type data:
    :return:
    :rtype:
    '''
    if isinstance(data, dict):
        sorted_data = sorted(data.items(), key=lambda x: x[0])
        message = ''.join(str(value) for _, value in sorted_data)
    elif isinstance(data, (list, tuple)):
        message = ''.join(str(value) for key, value in data)
    else:
        message = data
    return message.encode()


def generate_keys(mnemonic: str = None, private_key: str = None) -> tuple[str, str, str, str]:
    """
    Generates keys [public_key, private_key, mnemonic, ss58_address].
    """
    if private_key:
        keypair = Keypair.create_from_private_key(bytes.fromhex(private_key), ss58_format=42)
    else:
        mnemonic = mnemonic or Keypair.generate_mnemonic()
        keypair = Keypair.create_from_mnemonic(mnemonic)
    public_key = keypair.public_key.hex()
    private_key = keypair.private_key.hex()
    return public_key, private_key, mnemonic, keypair.ss58_address


def sign_message(private_key: str, data: Union[List, Dict, Tuple, str]) -> str:
    """
     Signs the message using the given private key and returns the signature result.

     Args:
         private_key (str): private key
         message (str): message to be signed

     Returns:
         bytes: signature result
     """
    keypair = Keypair.create_from_private_key(bytes.fromhex(private_key), ss58_format=42)
    match keypair.crypto_type:
        case KeypairType.SR25519:
            message = _format_data(data)
            signature: bytes = sr25519.sign(  # type: ignore
                (keypair.public_key, keypair.private_key), message)  # type: ignore
        case _:
            raise Exception(f"Crypto type {keypair.crypto_type} not supported")

    return signature.hex()


def verify_sign(pubkey: str, data, signature: str) -> bool:
    crypto_verify_fn = sr25519.verify
    message = _format_data(data)
    verified: bool = crypto_verify_fn(bytes.fromhex(signature), message, bytes.fromhex(pubkey))
    if not verified:
        # Another attempt with the data wrapped, as discussed in https://github.com/polkadot-js/extension/pull/743
        # Note: As Python apps are trusted sources on its own, no need to wrap data when signing from this lib
        verified: bool = crypto_verify_fn(  # type: ignore
            bytes.fromhex(signature), b'<Bytes>' + message + b'</Bytes>', bytes.fromhex(pubkey))
    return verified


def main():
    data = 'this a test text'
    public_key, private_key, mnemonic, ss58_address = generate_keys(
        'ordinary giraffe high drum walk seminar sun snack choice similar float bright')
    sign = sign_message(
        private_key,
        data)
    print(sign)
    verify = verify_sign(public_key, data, sign)
    print(verify)


if __name__ == '__main__':
    main()
