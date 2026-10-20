from config import API_HOST, API_PORT, validar_config

from Tratamento import coleta, controle, tratamento
from Categorizacao import categorizacao
from Saida import shets_consolidada
from Agente import ferramentas


# =========================================================
# PIPELINE PRINCIPAL
# =========================================================

def executar_pipeline():

    # -----------------------------------------------------
    # 1. COLETAR DADOS DAS PLANILHAS DE PESQUISA
    # -----------------------------------------------------

    dfs_brutos = coleta.coletar_todas_planilhas()

    if not dfs_brutos:
        return {
            "status": "sem_dados",
            "novos_registros": 0
        }

    # -----------------------------------------------------
    # 2. TRATAR E PADRONIZAR OS DADOS
    # -----------------------------------------------------

    consolidado_bruto = tratamento.tratar_lista_planilhas(
        dfs_brutos
    )

    # -----------------------------------------------------
    # 3. GERAR ID DOS REGISTROS
    # -----------------------------------------------------

    consolidado_bruto = controle.adicionar_id_registro(
        consolidado_bruto
    )

    # -----------------------------------------------------
    # 4. OBTER IDs JÁ PROCESSADOS
    # -----------------------------------------------------

    ids_processados = controle.obter_ids_processados()

    # -----------------------------------------------------
    # 5. IDENTIFICAR SOMENTE NOVOS REGISTROS
    # -----------------------------------------------------

    novos = controle.identificar_novos_registros(
        consolidado_bruto,
        ids_processados
    )

    if novos.empty:
        return {
            "status": "sem_novidades",
            "novos_registros": 0
        }

    # -----------------------------------------------------
    # 6. CATEGORIZAR PROBLEMAS/RECLAMAÇÕES COM LLM
    # -----------------------------------------------------

    novos_categorizados = (
        categorizacao.categorizar_dataframe(novos)
    )

    # -----------------------------------------------------
    # 7. SALVAR NA PLANILHA CONSOLIDADA
    # -----------------------------------------------------

    print("INICIANDO SALVAMENTO NA ABA DADOS...")

    shets_consolidada.salvar_novos_registros(
        novos_categorizados
    )

    print("SALVAMENTO NA ABA DADOS CONCLUÍDO!")
    # -----------------------------------------------------
    # 8. REGISTRAR OS REGISTROS COMO PROCESSADOS
    # -----------------------------------------------------

    controle.registrar_processamento(novos)

    # -----------------------------------------------------
    # 9. ATUALIZAR OS DADOS UTILIZADOS PELO AGENTE
    # -----------------------------------------------------

    ferramentas.forcar_recarga()

    # -----------------------------------------------------
    # 10. RETORNO
    # -----------------------------------------------------

    return {
        "status": "ok",
        "novos_registros": int(len(novos_categorizados))
    }


# =========================================================
# EXECUÇÃO LOCAL
# =========================================================


if __name__ == "__main__":
    validar_config()

    resultado = executar_pipeline()

    print(resultado)
