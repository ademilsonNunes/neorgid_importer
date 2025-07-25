import requests_mock
import pytest
from services.api_client import NeogridAPIClient


@pytest.fixture
def client():
    return NeogridAPIClient()


def test_buscar_pedidos_com_sucesso(client):
    mock_url = client.url
    mock_response = {
        "documents": [
            {
                "docId": "123456",
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
                            "itens": {
                                "item": [
                                    {
                                        "codigoProduto": "TESTE001",
                                        "descricaoProduto": "Produto de Teste",
                                        "quantidadePedida": "0000000000010.00",
                                        "precoLiquidoUnitario": "0000000000012.34",
                                        "valorLiquidoItem": "0000000000123.40",
                                        "aliquotaIPI": "005.00",
                                        "valorUnitarioIPI": "0000000000001.00",
                                        "referenciaProduto": "REF123",
                                        "unidadeMedida": "UN"
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(mock_url, json=mock_response, status_code=200)

        response = client.buscar_pedidos()
        assert "documents" in response
        assert len(response["documents"]) == 1
        assert response["documents"][0]["docId"] == "123456"
