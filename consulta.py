"""Entrada explícita para consulta real ou demonstração inteiramente local."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
from processamento import ler_pedidos, salvar_resultados, simular


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="Consulta de avaliações por pedido.")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--simular", action="store_true", help="Usa respostas fictícias locais.")
    modo.add_argument("--real", action="store_true", help="Acessa a interface configurada.")
    parser.add_argument("--entrada", help="CSV UTF-8 com a coluna Pedido.")
    parser.add_argument("--respostas", help="JSON fictício, somente na simulação.")
    parser.add_argument("--saida", help="Novo CSV dentro de outputs/; nunca sobrescreve.")
    args = parser.parse_args(argumentos)
    if not args.simular and not args.real:
        parser.print_help()
        return 0
    if not args.entrada:
        parser.error("informe --entrada")
    if args.simular and not args.respostas:
        parser.error("informe --respostas na simulação")
    if args.real and args.respostas:
        parser.error("--respostas é exclusivo da simulação")
    try:
        campos, pedidos = ler_pedidos(args.entrada)
        raiz = Path(__file__).resolve().parent / "outputs"
        sufixo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        nome = "simulacao" if args.simular else "consulta"
        saida = Path(args.saida).resolve() if args.saida else raiz / f"{nome}-{sufixo}.csv"
        if not saida.is_relative_to(raiz.resolve()):
            raise ValueError("A saída deve ficar dentro de outputs/ deste projeto.")
        if saida == Path(args.entrada).resolve():
            raise ValueError("Entrada e saída devem ser arquivos diferentes.")
        if saida.exists():
            raise ValueError("A saída já existe; escolha outro nome. Nenhum arquivo foi sobrescrito.")
        if args.simular:
            resultados = simular(pedidos, args.respostas)
        else:
            # Ajuda e simulação não importam os módulos de automação.
            from automacao import consultar
            resultados = consultar(pedidos)
        salvar_resultados(saida, campos, resultados)
    except (ValueError, OSError) as erro:
        detalhe = str(erro) if isinstance(erro, ValueError) else "Não foi possível ler/gravar os arquivos locais."
        print("Erro: " + detalhe)
        return 2
    except ImportError:
        print("Erro: as dependências do modo real não estão disponíveis.")
        return 2
    print("SIMULAÇÃO — respostas fictícias; nenhuma consulta externa." if args.simular else "Consulta concluída.")
    for estado in ("verificado", "Cancelado", "Pedido não encontrado", "Falha técnica"):
        print(f"{estado}: {sum(r['Status'] == estado for r in resultados)}")
    print(f"Registros: {len(resultados)}. CSV separado: {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
