import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.main import processar_pedido_neogrid
from models.cliente import Cliente
from models.pedido_sobel import PedidoSobel

class FakeProcessadorPedido:
    def __init__(self):
        self.recebido = None
    def processar(self, data):
        self.recebido = data
        cliente_data = {
            "CODIGO": "1",
            "RAZAOSOCIAL": "Teste",
            "CGCCPF": "00000000000000",
            "INSCR_ESTADUAL": "",
            "ENDERECO": "",
            "CODIGONOMECIDADE": "",
            "ESTADO": "",
            "BAIRRO": "",
            "TELEFONE": "",
            "FAX": "",
            "CEP": "",
            "CODIGOSTATUSCLI": "0",
            "NOMEFANTASIA": "Teste",
            "DATACADASTRO": "",
            "CODIGOENDENTREGA": "",
            "CODIGOREGIAO": 0,
            "CODIGOANALCLIENTE": "",
            "CODIGOTABPRECO": "",
            "CODIGOCONDPAGTO": "",
            "CODIGOCLIENTEPAI": "",
            "OBSFETCHATURAMENTO": "",
            "EMAILCOPIAPEDIDO": "",
            "FLAGENVIACOPIAPEDIDO": "",
            "CESP_FLAGENTREGAAGENDADA": 0,
            "Cesp_QtdeDiasMinEntrega": "0"
        }
        cliente = Cliente.from_dict(cliente_data)
        return PedidoSobel.from_json(data, cliente, [])

class FakeRepo:
    def __init__(self):
        self.inserido = None
    def inserir_pedido(self, pedido):
        self.inserido = pedido
        return True
    def log_processamento(self, *args, **kwargs):
        pass


def test_processa_pedido_registra_campos():
    doc = {
        "docId": "DOC123",
        "content": [
            {
                "order": {
                    "cabecalho": {
                        "numeroPedidoComprador": "99999",
                        "cnpjComprador": "12345678000199",
                        "cnpjFornecedor": "98765432000100",
                        "dataHoraEmissao": "150720250000",
                        "dataHoraInicialEntrega": "310720250000",
                        "condicaoEntrega": "CIF"
                    },
                    "pagamento": {
                        "condicaoPagamento": "1",
                        "dataVencimento": "20250720"
                    },
                    "sumario": {
                        "valorTotalPedido": "0000000001234.56",
                        "valorTotalIPI": "0000000000010.00"
                    },
                    "itens": {"item": []}
                }
            }
        ]
    }
    proc = FakeProcessadorPedido()
    repo = FakeRepo()

    resultado = processar_pedido_neogrid(doc, proc, repo)

    assert repo.inserido.doc_id == "DOC123"
    assert repo.inserido.ordem_compra == "99999"
    assert resultado["status"] == "sucesso"
