"""CSV e estados de resultado, sem dependências externas ou efeitos de importação."""
import csv
import json
from pathlib import Path

ESTADOS = {"verificado": "verificado", "cancelado": "Cancelado",
           "ausente": "Pedido não encontrado", "erro_tecnico": "Falha técnica"}


def ler_pedidos(arquivo):
    try:
        with Path(arquivo).open(encoding="utf-8-sig", newline="") as entrada:
            leitor = csv.DictReader(entrada, strict=True)
            campos = leitor.fieldnames
            if not campos or "Pedido" not in campos:
                raise ValueError("Coluna obrigatória ausente: Pedido.")
            if len(campos) != len(set(campos)):
                raise ValueError("Cabeçalhos repetidos no CSV.")
            pedidos = []
            for numero, linha in enumerate(leitor, 1):
                if None in linha or any(v is None for v in linha.values()):
                    raise ValueError(f"Registro {numero}: quantidade de campos incompatível.")
                if not linha["Pedido"].strip():
                    raise ValueError(f"Registro {numero}: Pedido não pode ficar vazio.")
                pedidos.append(linha)
            return campos, pedidos
    except (UnicodeError, csv.Error):
        raise ValueError("CSV incompatível: use UTF-8 e estrutura CSV válida.") from None


def resultado(pedido, estado, score="", simulado=False):
    if not isinstance(estado, str) or estado not in ESTADOS:
        raise ValueError("Estado de resposta incompatível.")
    if estado == "verificado" and (not isinstance(score, str) or not score.strip()):
        raise ValueError("Resposta verificada exige avaliação textual preenchida.")
    linha = dict(pedido)
    linha["Score"] = score.replace(".", ",") if estado == "verificado" else "N/E"
    linha["Status"] = ESTADOS[estado]
    linha["Origem"] = "Simulado" if simulado else "Consulta real"
    linha["Detalhe"] = {
        "verificado": "Avaliação extraída da resposta.",
        "cancelado": "Cancelamento indicado explicitamente.",
        "ausente": "Ausência indicada explicitamente.",
        "erro_tecnico": "Consulta sem confirmação; não significa ausência do pedido.",
    }[estado]
    return linha


def simular(pedidos, arquivo):
    try:
        payload = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError("Respostas fictícias devem usar JSON UTF-8 válido.") from None
    if not isinstance(payload, dict) or payload.get("simulado") is not True or not isinstance(payload.get("respostas"), list):
        raise ValueError("Respostas devem declarar simulado=true e uma lista respostas.")
    respostas = {}
    for item in payload["respostas"]:
        if not isinstance(item, dict) or not isinstance(item.get("Pedido"), str) or not item["Pedido"].strip():
            raise ValueError("Resposta fictícia exige Pedido textual preenchido.")
        if item["Pedido"] in respostas:
            raise ValueError("Respostas repetidas para o mesmo Pedido.")
        if not isinstance(item.get("Estado"), str) or item["Estado"] not in ESTADOS:
            raise ValueError("Estado fictício incompatível.")
        resultado({"Pedido": item["Pedido"]}, item["Estado"], item.get("Score", ""), True)
        respostas[item["Pedido"]] = item
    return [resultado(p, respostas[p["Pedido"]]["Estado"], respostas[p["Pedido"]].get("Score", ""), True)
            if p["Pedido"] in respostas else resultado(p, "erro_tecnico", simulado=True) for p in pedidos]


def salvar_resultados(arquivo, campos, resultados):
    campos_saida = list(campos) + [c for c in ("Score", "Status", "Origem", "Detalhe") if c not in campos]
    path = Path(arquivo)
    path.parent.mkdir(parents=True, exist_ok=True)
    criado = False
    try:
        with path.open("x", encoding="utf-8", newline="") as saida:
            criado = True
            escritor = csv.DictWriter(saida, fieldnames=campos_saida, lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(resultados)
    except Exception:
        if criado:
            path.unlink(missing_ok=True)
        raise
