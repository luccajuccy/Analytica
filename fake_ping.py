# -*- coding: utf-8 -*-
"""
fake_ping.py — Simulação de ping e verificação de porta de rede
EVT Analytica — Dados fictícios para demonstração

Funções:
  • ping_ip(ip)           → True (online ~90%) / False (offline ~10%)
  • check_port(ip, port)  → True / False

A seed é baseada no IP + minuto atual, garantindo que o mesmo
IP retorne o mesmo status dentro do mesmo minuto (consistência
visual no dashboard sem estado persistente).
"""

import hashlib
from datetime import datetime


def _deterministic_random(ip: str, salt: str = '') -> float:
    """
    Gera um float pseudo-aleatório em [0, 1) de forma determinística
    com base no IP, no minuto atual e em um salt opcional.

    O resultado é estável durante o mesmo minuto-calendário,
    evitando "flickering" no painel de monitoramento.

    Parâmetros
    ----------
    ip : str
        Endereço IP (ex.: ``10.0.0.101``).
    salt : str
        Valor extra para diferenciar chamadas distintas (ex.: porta).

    Retorna
    -------
    float — Valor em [0.0, 1.0).
    """
    now = datetime.now()
    # Chave = ip + minuto arredondado + salt
    key = f"{ip}:{now.strftime('%Y%m%d%H%M')}:{salt}"
    digest = hashlib.md5(key.encode('utf-8')).hexdigest()
    # Converter primeiros 8 caracteres hex para float normalizado
    return int(digest[:8], 16) / 0xFFFFFFFF


def ping_ip(ip: str) -> bool:
    """
    Simula ``ping`` para um endereço IP.

    Retorna ``True`` (online) ~90% das vezes e ``False`` (offline)
    ~10%, de forma determinística dentro do mesmo minuto.

    Parâmetros
    ----------
    ip : str
        Endereço IP privado/fictício (ex.: ``10.0.0.101``).

    Retorna
    -------
    bool — ``True`` se o host está "respondendo".
    """
    return _deterministic_random(ip, salt='ping') < 0.90


def check_port(ip: str, port: int = 80) -> bool:
    """
    Simula verificação de conexão TCP (``socket.connect``).

    Comportamento similar ao ``ping_ip``, mas usa a porta como
    parte da seed, permitindo que portas diferentes do mesmo IP
    tenham resultados independentes.

    Parâmetros
    ----------
    ip : str
        Endereço IP.
    port : int
        Porta TCP a verificar (padrão: 80).

    Retorna
    -------
    bool — ``True`` se a porta está "aberta".
    """
    return _deterministic_random(ip, salt=f'port{port}') < 0.90


# =====================================================================
# Execução direta para testes rápidos
# =====================================================================
if __name__ == "__main__":
    print("=" * 50)
    print("  TESTE — fake_ping.py")
    print("=" * 50)

    test_ips = [f"10.0.0.{i}" for i in range(101, 121)]
    for ip in test_ips:
        online = ping_ip(ip)
        port_ok = check_port(ip, 502)
        status = "ONLINE" if online else "OFFLINE"
        port_status = "ABERTA" if port_ok else "FECHADA"
        print(f"  {ip:15s}  ping={status:7s}  porta 502={port_status}")
