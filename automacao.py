"""Modo real, dependente dos seletores e da interface configurados pelo operador."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from processamento import resultado


def configuracao():
    nomes = ("CONSULTA_URL", "CONSULTA_DRIVER", "CONSULTA_USUARIO", "CONSULTA_SENHA", "CONSULTA_SELETORES")
    ausentes = [n for n in nomes if not os.environ.get(n, "").strip()]
    if ausentes:
        raise ValueError("Defina no ambiente: " + ", ".join(ausentes))
    config = {n: os.environ[n] for n in nomes}
    try:
        url = urlsplit(config["CONSULTA_URL"])
    except ValueError:
        raise ValueError("CONSULTA_URL tem formato incompatível.") from None
    if url.scheme not in ("http", "https") or not url.netloc or url.username or url.password:
        raise ValueError("CONSULTA_URL deve ser HTTP(S), sem credenciais embutidas.")
    if not Path(config["CONSULTA_DRIVER"]).is_file():
        raise ValueError("CONSULTA_DRIVER deve apontar para um arquivo de chromedriver.")
    try:
        seletores = json.loads(Path(config["CONSULTA_SELETORES"]).read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("CONSULTA_SELETORES deve apontar para JSON UTF-8 válido.") from None
    obrigatorios = ("usuario", "senha", "historico", "busca", "concluido", "avaliacao", "fechar", "cancelado")
    if not isinstance(seletores, dict) or any(not isinstance(seletores.get(k), str) or not seletores[k].strip() for k in obrigatorios):
        raise ValueError("Seletores obrigatórios ausentes ou incompatíveis.")
    if not isinstance(seletores.get("ausente", ""), str):
        raise ValueError("O seletor opcional ausente deve ser texto.")
    return config, seletores


def consultar(pedidos):
    config, seletores = configuracao()
    # Imports e navegador somente após seleção explícita do modo real/configuração.
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from time import sleep
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(executable_path=config["CONSULTA_DRIVER"]))
        espera = WebDriverWait(driver, 30)
        driver.get(config["CONSULTA_URL"])
        usuario = espera.until(EC.element_to_be_clickable((By.XPATH, seletores["usuario"])))
        usuario.clear()
        usuario.send_keys(config["CONSULTA_USUARIO"])
        senha = driver.find_element(By.XPATH, seletores["senha"])
        senha.clear()
        senha.send_keys(config["CONSULTA_SENHA"], Keys.ENTER)
        espera.until(EC.element_to_be_clickable((By.XPATH, seletores["historico"]))).click()
        saida = []
        for pedido in pedidos:
            aberto = False
            try:
                busca = espera.until(EC.element_to_be_clickable((By.XPATH, seletores["busca"])))
                busca.click()
                busca.clear()
                busca.send_keys(pedido["Pedido"])
                sleep(2)

                def resposta_visivel(navegador):
                    encontrados = []
                    for estado, chave in (("verificado", "concluido"), ("cancelado", "cancelado"), ("ausente", "ausente")):
                        if not seletores.get(chave):
                            continue
                        visiveis = [e for e in navegador.find_elements(By.XPATH, seletores[chave]) if e.is_displayed()]
                        if visiveis:
                            encontrados.append((estado, visiveis[0]))
                    if len(encontrados) > 1:
                        raise ValueError("Resposta ambígua na interface.")
                    return encontrados[0] if encontrados else False

                estado, elemento = espera.until(resposta_visivel)
                score = ""
                if estado == "verificado":
                    elemento.click()
                    aberto = True
                    score = espera.until(EC.visibility_of_element_located((By.XPATH, seletores["avaliacao"]))).text
                linha = resultado(pedido, estado, score)
            except Exception:
                linha = resultado(pedido, "erro_tecnico")
            finally:
                if aberto:
                    try:
                        driver.find_element(By.XPATH, seletores["fechar"]).click()
                    except Exception:
                        linha = resultado(pedido, "erro_tecnico")
            saida.append(linha)
        return saida
    except Exception:
        raise ValueError("Falha técnica ao iniciar ou navegar na interface configurada; nenhum resultado confirmado.") from None
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
