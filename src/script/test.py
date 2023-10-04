import os
from os import path
import random
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

import mylib
path = os.getcwd() #　C:\workspace\server\src\script
print(path)
print(os.path.join([path,"abc","cde"]))