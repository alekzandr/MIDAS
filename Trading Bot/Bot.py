from Config import *
import pyotp

totp  = pyotp.TOTP("My2factorAppHere").now()