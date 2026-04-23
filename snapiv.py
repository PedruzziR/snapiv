import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ================= BLOCO 1: DEFINIÇÃO DA MARCA D'ÁGUA =================
def inject_watermark(nome_paciente, id_sessao):
    paciente_display = nome_paciente if nome_paciente else "PACIENTE NÃO IDENTIFICADO"
    
    watermark_style = f"""
    <style>
    .watermark {{
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 9999;
        pointer-events: none;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
        align-content: space-around;
        opacity: 0.12;
        user-select: none;
    }}
    .watermark-text {{
        transform: rotate(-45deg);
        font-size: 22px;
        font-weight: bold;
        color: grey;
        white-space: nowrap;
        text-align: center;
        margin: 40px;
    }}
    </style>
    <div class="watermark">
        {f"<div class='watermark-text'>INSTRUMENTO SIGILOSO<br>{paciente_display}<br>{id_sessao}</div>" * 20}
    </div>
    """
    st.markdown(watermark_style, unsafe_allow_html=True)

# ================= CONFIGURAÇÕES DE E-MAIL =================
SEU_EMAIL = st.secrets["EMAIL_USUARIO"]
SENHA_DO_EMAIL = st.secrets["SENHA_USUARIO"]

# ================= CONEXÃO COM GOOGLE SHEETS =================
@st.cache_resource
def conectar_planilha():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
    client = gspread.authorize(creds)
    return client.open("Controle_Tokens").sheet1 

try:
    planilha = conectar_planilha()
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

def enviar_email_resultados(nome_pac, token, nome_resp, vinculo, contagem_desatencao, res_desatencao, contagem_hiper, res_hiper):
    assunto = f"Resultados Escala SNAP-IV - Paciente: {nome_pac}"
    corpo = f"Avaliação Escala SNAP-IV concluída.\n\n=== DADOS DO(A) PACIENTE ===\nNome: {nome_pac}\nToken: {token}\n\n"
    corpo += f"=== DADOS DO(A) RESPONDENTE ===\nNome: {nome_resp}\nVínculo: {vinculo}\n\n"
    corpo += f"================ RESULTADOS ================\n\n"
    corpo += f"► DESATENÇÃO: {contagem_desatencao}/9 ({res_desatencao})\n"
    corpo += f"► HIPERATIVIDADE/IMPULSIVIDADE: {contagem_hiper}/9 ({res_hiper})\n"

    msg = MIMEMultipart()
    msg['From'] = SEU_EMAIL
    msg['To'] = "psicologabrunaligoski@gmail.com"
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SEU_EMAIL, SENHA_DO_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# ESTRUTURA
perguntas = [
    "Não consegue prestar muita atenção a detalhes ou comete erros por descuido nos trabalhos da escola ou tarefas.",
    "Tem dificuldade de manter a atenção em tarefas ou atividades de lazer.",
    "Parece não estar ouvindo quando se fala diretamente com ele(a).",
    "Não segue instruções até o fim e não termina deveres de escola, tarefas ou obrigações.",
    "Tem dificuldade para organizar tarefas e atividades.",
    "Evita, não gosta ou se envolve contra a vontade em tarefas que exigem esforço mental prolongado.",
    "Perde coisas necessárias para atividades (brinquedos, deveres da escola, lápis ou livros).",
    "Distrai-se com estímulos externos.",
    "É esquecido(a) em atividades do dia a dia.",
    "Mexe com as mãos ou os pés ou se remexe na cadeira.",
    "Sai do lugar na sala de aula ou em outras situações em que se espera que fique sentado(a).",
    "Corre de um lado para o outro ou sobe demais nas coisas em situações em que isto é inapropriado.",
    "Tem dificuldade em brincar ou envolver-se em atividades de lazer de forma calma.",
    "Não para ou frequentemente está a “mil por hora”.",
    "Fala em excesso.",
    "Responde perguntas de forma precipitada antes que elas tenham sido terminadas.",
    "Tem dificuldade em esperar sua vez.",
    "Interrompe os outros ou se intromete (nas conversas, jogos, etc.)."
]
opcoes_respostas = ["Nem um pouco.", "Só um pouco.", "Bastante.", "Demais."]

st.set_page_config(page_title="Escala SNAP-IV", layout="centered")

# ================= VALIDAÇÃO E CAPTURA DE PARÂMETROS =================
parametros = st.query_params
token_url = parametros.get("token", None)
nome_na_url = parametros.get("nome", "")

if not token_url:
    st.warning("⚠️ Link de acesso inválido.")
    st.stop()

try:
    registros = planilha.get_all_records()
    dados_token = None
    linha_alvo = 2 
    for i, reg in enumerate(registros):
        if str(reg.get("Token")) == token_url:
            dados_token = reg
            linha_alvo += i
            break
            
    if not dados_token or dados_token.get("Status") != "Aberto":
        st.error("⚠️ Este link é inválido ou já foi utilizado.")
        st.stop()
except Exception:
    st.error("Erro técnico na validação do acesso.")
    st.stop()

# ================= INTERFACE =================
st.markdown("<h1 style='text-align: center;'>Clínica Bruna Ligoski</h1>", unsafe_allow_html=True)

if st.session_state.get("avaliacao_concluida", False):
    st.success("Avaliação enviada com sucesso!")
    st.stop()

# IDENTIFICAÇÃO (FORA DO FORM)
st.subheader("Dados de Identificação")
nome_paciente = st.text_input("Nome completo do(a) paciente *", value=nome_na_url)
nome_respondente = st.text_input("Nome completo do(a) respondente *")
vinculo_respondente = st.text_input("Vínculo (ex.: mãe, pai, professor(a), etc.) *")

# Marca d'água dinâmica
inject_watermark(nome_paciente, token_url)

st.divider()

with st.form("form_snap_iv"):
    respostas_coletadas = {}
    for index, texto_pergunta in enumerate(perguntas):
        num_q = index + 1
        st.write(f"**{num_q}. {texto_pergunta}**")
        respostas_coletadas[num_q] = st.radio(f"Oculto {num_q}", opcoes_respostas, index=None, label_visibility="collapsed")
        st.divider()

    if st.form_submit_button("Enviar Avaliação"):
        questoes_em_branco = [q for q, r in respostas_coletadas.items() if r is None]
        if not nome_paciente or not nome_respondente or not vinculo_respondente:
            st.error("Preencha todos os dados de identificação.")
        elif questoes_em_branco:
            st.error(f"Responda todas as perguntas. Faltam {len(questoes_em_branco)}.")
        else:
            contagem_desatencao = sum(1 for q in range(1, 10) if respostas_coletadas[q] in ["Bastante.", "Demais."])
            contagem_hiper = sum(1 for q in range(10, 19) if respostas_coletadas[q] in ["Bastante.", "Demais."])
            
            res_desatencao = "Clínico" if contagem_desatencao >= 6 else "Não Clínico"
            res_hiper = "Clínico" if contagem_hiper >= 6 else "Não Clínico"

            if enviar_email_resultados(nome_paciente, token_url, nome_respondente, vinculo_respondente, contagem_desatencao, res_desatencao, contagem_hiper, res_hiper):
                planilha.update_cell(linha_alvo, 5, "Respondido")
                st.session_state.avaliacao_concluida = True
                st.rerun()
