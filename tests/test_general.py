import os
import re
import pytest
import collections

from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_FOLDER = 'tf'
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load('''
    otype g_cons sign cert''')
api.loadLog()
api.makeAvailableIn(globals())

F, L = api.F, api.L

##Sign
def test_certainty_x():
    assert all({F.cert.v(n) != 'True' for n in F.otype.s('sign') if F.sign.v(n)=='x'})