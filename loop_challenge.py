"""
Loop Challenge - Automação e Programabilidade em Redes

Uso:
    export API_TOKEN="seu-token"        # Linux/macOS
    set API_TOKEN=seu-token             # Windows (cmd)
    python loop_challenge.py            # usa maxIterations=10
    python loop_challenge.py 5          # usa maxIterations=5

Se você já tem a função de login da aula anterior, substitua a função
obter_token() abaixo pela sua.
"""
import os
import sys
import time
import logging

import requests

URL = "https://api.wagnerloch.com.br/challenges/loop"
TIMEOUT_HTTP = 15          # segundos
MARGEM = 0.3               # espera extra (s) para nunca enviar cedo demais
MAX_TENTATIVAS_REDE = 3    # retries em caso de erro de conexão

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("loop")


def obter_token() -> str:
    """Troque por o código de autenticação da aula anterior, se preferir."""
    token = os.environ.get("API_TOKEN")
    if not token:
        sys.exit("Defina a variável de ambiente API_TOKEN com o seu token.")
    return token


def requisitar(token: str, max_iterations: int) -> dict:
    """Faz o POST com retry apenas para falhas de rede."""
    headers = {"Authorization": f"Bearer {token}"}
    body = {"maxIterations": max_iterations}

    for tentativa in range(1, MAX_TENTATIVAS_REDE + 1):
        try:
            resp = requests.post(URL, json=body, headers=headers, timeout=TIMEOUT_HTTP)
            log.info("HTTP %s", resp.status_code)
            return resp.json()
        except (requests.ConnectionError, requests.Timeout) as erro:
            log.warning("Falha de rede (%s/%s): %s", tentativa, MAX_TENTATIVAS_REDE, erro)
            time.sleep(1)
    raise RuntimeError("Não foi possível conectar à API.")


def main() -> None:
    max_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    token = obter_token()

    # 1) Requisição inicial
    inicio = time.monotonic()
    dados = requisitar(token, max_iterations)

    while True:
        status = dados.get("status")
        log.info("%s | %s | %s", status, dados.get("progress", "-"), dados.get("message"))

        if status == "SUCCESS":
            log.info("Desafio concluído!")
            return

        if status in ("TOO_EARLY", "TOO_LATE"):
            log.error("Desafio resetado. Rode o script novamente.")
            return

        if status not in ("START", "CONTINUE"):
            log.error("Resposta inesperada: %s", dados)
            return

        # 2) Espera o tempo exato pedido pelo servidor, descontando o tempo
        #    já gasto desde a última requisição (latência + processamento).
        espera = dados["nextWaitTimeInSeconds"]
        alvo = inicio + espera + MARGEM
        restante = alvo - time.monotonic()
        log.info("Aguardando %.2fs...", max(restante, 0))
        if restante > 0:
            time.sleep(restante)

        # 3) Próxima requisição
        inicio = time.monotonic()
        dados = requisitar(token, max_iterations)


if __name__ == "__main__":
    main()
