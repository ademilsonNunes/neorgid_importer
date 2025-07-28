import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.helpers import interpretar_codigo_produto


def test_interpretar_codigo_produto_ean13():
    ean, dun, cod = interpretar_codigo_produto("7896524726150")
    assert ean == "7896524726150"
    assert dun == ""
    assert cod == ""


def test_interpretar_codigo_produto_dun14():
    ean, dun, cod = interpretar_codigo_produto("17896524703332")
    assert ean == ""
    assert dun == "17896524703332"
    assert cod == ""


def test_interpretar_codigo_produto_codigo_interno():
    ean, dun, cod = interpretar_codigo_produto("1001.01.03X05L")
    assert ean == ""
    assert dun == ""
    assert cod == "1001.01.03X05L"
