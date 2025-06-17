# -*- coding: utf-8 -*-
"""Utilidades para consulta à API da Câmara dos Deputados."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from IPython.display import HTML, display

# URL base da API de Dados Abertos da Câmara dos Deputados
URL_BASE = "https://dadosabertos.camara.leg.br/api/v2"

# Siglas dos estados brasileiros
SIGLAS_ESTADOS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO",
]


def _chamar_api(url: str, timeout: int = 20, max_tentativas: int = 3, espera: int = 3) -> Optional[Dict[str, Any]]:
    """Realiza uma requisição GET e retorna o JSON ou ``None`` em caso de falha."""
    for tentativa in range(1, max_tentativas + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.RequestException, ValueError) as exc:
            print(f"Erro na requisição '{url}' (tentativa {tentativa}/{max_tentativas}): {exc}")
            if tentativa < max_tentativas:
                time.sleep(espera)
    return None


# ---------------------------------------------------------------------------
# Funções de consulta
# ---------------------------------------------------------------------------

def obter_deputados_por_estado(sigla_uf: str) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
    """Retorna todos os deputados de uma UF."""
    deputados: List[Dict[str, Any]] = []
    pagina = 1
    while True:
        url = f"{URL_BASE}/deputados?siglaUf={sigla_uf}&itens=100&pagina={pagina}"
        dados = _chamar_api(url)
        if not dados:
            return False, None
        if not dados.get("dados"):
            break
        deputados.extend(dados["dados"])
        if not any(link.get("rel") == "next" for link in dados.get("links", [])):
            break
        pagina += 1
    return True, deputados


def obter_detalhes_deputado(id_deputado: int) -> Optional[Dict[str, Any]]:
    url = f"{URL_BASE}/deputados/{id_deputado}"
    return _chamar_api(url)


def obter_profissoes_deputado(id_deputado: int) -> Optional[Dict[str, Any]]:
    url = f"{URL_BASE}/deputados/{id_deputado}/profissoes"
    return _chamar_api(url)


def obter_ocupacoes_deputado(id_deputado: int) -> Optional[Dict[str, Any]]:
    url = f"{URL_BASE}/deputados/{id_deputado}/ocupacoes"
    return _chamar_api(url)


def obter_mandatos_externos_deputado(id_deputado: int) -> Optional[Dict[str, Any]]:
    url = f"{URL_BASE}/deputados/{id_deputado}/mandatosExternos"
    return _chamar_api(url)


# ---------------------------------------------------------------------------
# Formatação HTML
# ---------------------------------------------------------------------------

def formatar_perfil_completo_html(
    detalhes: Dict[str, Any],
    profissoes: Optional[Dict[str, Any]] = None,
    ocupacoes: Optional[Dict[str, Any]] = None,
    mandatos: Optional[Dict[str, Any]] = None,
    frentes: Optional[Dict[str, Any]] = None,
) -> str:
    """Monta o HTML do perfil do deputado."""
    if not detalhes or not detalhes.get("dados"):
        return "<h3>Não foi possível obter os detalhes do deputado.</h3>"

    dados = detalhes.get("dados", {})
    status = dados.get("ultimoStatus", {})
    gabinete = status.get("gabinete", {})

    nome_eleitoral = status.get("nomeEleitoral", "Nome não informado")
    url_foto = status.get("urlFoto", "")
    partido_uf = f"{status.get('siglaPartido', 'N/A')} - {status.get('siglaUf', 'N/A')}"

    data_nasc_str = dados.get("dataNascimento")
    data_nasc_formatada = (
        datetime.strptime(data_nasc_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        if data_nasc_str else "Não informada"
    )

    data_status_str = status.get("data")
    data_status_formatada = (
        datetime.strptime(data_status_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        if data_status_str else "Não informada"
    )

    html_string = f"""
    <style>
        .profile-card {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 24px;
            max-width: 800px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background-color: #fff;
            margin: 20px;
        }}
        .profile-header {{
            display: flex;
            align-items: center;
            border-bottom: 1px solid #eee;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .profile-header img {{
            width: 110px;
            height: 110px;
            border-radius: 50%;
            margin-right: 24px;
            border: 3px solid #f0f0f0;
        }}
        .profile-header .header-text h2 {{ margin: 0; font-size: 28px; color: #333; }}
        .profile-header .header-text h3 {{ margin: 5px 0 0 0; font-size: 20px; font-weight: 400; color: #666; }}
        .profile-section h4 {{
            margin-top: 24px;
            margin-bottom: 12px;
            font-size: 18px;
            color: #0056b3;
            border-bottom: 2px solid #0056b3;
            padding-bottom: 6px;
        }}
        .profile-section ul {{ list-style-type: none; padding-left: 0; margin: 0; }}
        .profile-section li {{
            font-size: 15px;
            padding: 8px 0;
            border-bottom: 1px solid #f7f7f7;
            display: flex;
        }}
        .profile-section li:last-child {{ border-bottom: none; }}
        .profile-section strong {{ color: #333; width: 180px; flex-shrink: 0; }}
        .social-links a {{ display: block; text-decoration: none; color: #007bff; }}
    </style>
    <div class="profile-card">
        <div class="profile-header">
            <img src="{url_foto}" alt="Foto de {nome_eleitoral}">
            <div class="header-text">
                <h2>{nome_eleitoral}</h2>
                <h3>{partido_uf}</h3>
            </div>
        </div>
    """

    # Resumo do Mandato
    html_string += f"""
        <div class="profile-section">
            <h4>Resumo do Mandato</h4>
            <ul>
                <li><strong>Situação:</strong> {status.get('situacao', 'Não informada')}</li>
                <li><strong>Condição Eleitoral:</strong> {status.get('condicaoEleitoral', 'Não informada')}</li>
                <li><strong>Legislatura:</strong> {status.get('idLegislatura', 'Não informada')}</li>
                <li><strong>Status desde:</strong> {data_status_formatada}</li>
            </ul>
        </div>
    """

    # Gabinete e Contatos
    redes_sociais_lista = dados.get("redeSocial", [])
    html_string += f"""
        <div class="profile-section">
            <h4>Gabinete e Contatos</h4>
            <ul>
                <li><strong>Localização:</strong> Prédio {gabinete.get('predio', '?')}, sala {gabinete.get('sala', '?')} ({gabinete.get('andar', '?')}º andar)</li>
                <li><strong>Telefone:</strong> {gabinete.get('telefone', 'Não informado')}</li>
                <li><strong>Email:</strong> {gabinete.get('email', 'Não informado')}</li>
    """
    if dados.get("urlWebsite"):
        site = dados.get("urlWebsite")
        html_string += f"<li><strong>Website:</strong> <a href='{site}' target='_blank'>{site}</a></li>"
    if redes_sociais_lista:
        links_html = "".join(
            [f"<a href='{rede}' target='_blank'>{rede}</a>" for rede in redes_sociais_lista]
        )
        html_string += f"<li class='social-links'><strong>Redes Sociais:</strong><br>{links_html}</li>"
    html_string += "</ul></div>"

    # Informações Pessoais
    html_string += f"""
        <div class="profile-section">
            <h4>Informações Pessoais</h4>
            <ul>
                <li><strong>Nome Civil:</strong> {dados.get('nomeCivil', 'Não informado')}</li>
                <li><strong>Data de Nascimento:</strong> {data_nasc_formatada}</li>
                <li><strong>Sexo:</strong> {'Feminino' if dados.get('sexo') == 'F' else 'Masculino'}</li>
                <li><strong>Naturalidade:</strong> {dados.get('municipioNascimento', 'N/A')} - {dados.get('ufNascimento', 'N/A')}</li>
                <li><strong>Escolaridade:</strong> {dados.get('escolaridade', 'Não informada')}</li>
    """
    if dados.get("dataFalecimento"):
        html_string += f"<li><strong>Data de Falecimento:</strong> {dados.get('dataFalecimento')}</li>"
    html_string += "</ul></div>"

    # Atuação Profissional e Pública
    if (profissoes and profissoes.get("dados")) or (mandatos and mandatos.get("dados")):
        html_string += "<div class='profile-section'><h4>Atuação Profissional e Pública</h4><ul>"
        profissoes_lista = [p["titulo"] for p in profissoes["dados"]] if profissoes and profissoes.get("dados") else []
        if profissoes_lista:
            html_string += f"<li><strong>Profissões:</strong> {', '.join(profissoes_lista)}</li>"
        if mandatos and mandatos.get("dados"):
            for m in mandatos["dados"]:
                html_string += (
                    f"<li><strong>Mandato Anterior:</strong> {m.get('cargo', '')} "
                    f"em {m.get('municipio', '')}/{m.get('uf', '')} ({m.get('anoInicio', '')}-{m.get('anoFim', '')})</li>"
                )
        html_string += "</ul></div>"

    if frentes and frentes.get("dados"):
        html_string += "<div class='profile-section'><h4>Atuação Parlamentar</h4><ul>"
        frentes_lista = [f['titulo'] for f in frentes['dados']]
        html_string += f"<li><strong>Participa de Frentes:</strong> {len(frentes_lista)} frentes</li>"
        html_string += "</ul></div>"

    html_string += "</div>"
    return html_string


# ---------------------------------------------------------------------------
# Exemplo de uso
# ---------------------------------------------------------------------------

def exibir_perfil_completo_deputado(id_deputado: int) -> None:
    """Obtém os dados de um deputado e exibe seu perfil em HTML."""
    print(f"Buscando perfil completo para o deputado ID: {id_deputado}...")
    detalhes = obter_detalhes_deputado(id_deputado)
    profissoes = obter_profissoes_deputado(id_deputado)
    ocupacoes = obter_ocupacoes_deputado(id_deputado)
    mandatos = obter_mandatos_externos_deputado(id_deputado)

    if not detalhes:
        print("Não foi possível continuar, pois os detalhes básicos do deputado não foram encontrados.")
        return

    perfil_html = formatar_perfil_completo_html(detalhes, profissoes, ocupacoes, mandatos)
    display(HTML(perfil_html))
    print("Busca finalizada.")


if __name__ == "__main__":
    id_deputado_exemplo = 220559
    exibir_perfil_completo_deputado(id_deputado_exemplo)
