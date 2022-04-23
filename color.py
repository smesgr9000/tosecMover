#!/usr/bin/python

from colorama import Fore, Back, Style

def cDim(value: str) -> str:
    return Style.DIM + value + Style.NORMAL
def cRed(value: str) -> str:
    return Fore.RED + value + Fore.RESET
def cGreen(value: str) -> str:
    return Fore.GREEN + value + Fore.RESET
def cYellow(value: str) -> str:
    return Fore.YELLOW + value + Fore.RESET
