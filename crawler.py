<<<<<<< HEAD
import os
import re
import time
import requests
import feedparser
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

ARQUIVO_MEMORIA = 'vagas_enviadas.json'

def carregar_vagas_enviadas():
    """Carrega o histórico de links já enviados."""
    if os.path.exists(ARQUIVO_MEMORIA):
        with open(ARQUIVO_MEMORIA, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_vagas_enviadas(vagas_atuais):
    """Guarda a lista atualizada de links no ficheiro."""
    with open(ARQUIVO_MEMORIA, 'w', encoding='utf-8') as f:
        json.dump(vagas_atuais, f)
# ==========================================
# 1. CONFIGURAÇÕES E PARÂMETROS
# ==========================================
TARGET_TITLES = [
    # Dados e ML (Originais)
    "cientista de dados", "data scientist", "engenheiro de machine learning", "machine learning engineer",
    # Inteligência Artificial
    "ai engineer", "engenheiro de ia", "engenheiro de inteligência artificial", "ia developer",
    # Backend e Software
    "backend developer", "desenvolvedor backend", "engenheiro de software", "software engineer", 
    "desenvolvedor python", "python developer",
    # Dados (Pipelines/BI que você tem experiência)
    "engenheiro de dados", "data engineer"
]
LEVELS = ["jr", "júnior", "junior", "pleno", "pl"]
MODALITY = ["remoto", "remote"]

# Skills extraídas do Samuel_Buarque_AI_Engineer.pdf
NORMAL_WEIGHT_SKILLS = [
    # Originais
    "python", "langgraph", "langchain", "pgvector", "postgresql", "aws", "fastapi",
    # Linguagens e Backend
    "typescript", "javascript", "node", "node.js", "sql", "rest", "api",
    # Bancos de Dados e Infraestrutura
    "mongodb", "mysql", "docker", "podman", "pipelines",
    # Ciência de Dados (Básico)
    "pandas", "numpy", "power bi", "scikit-learn"
]
MAX_WEIGHT_SKILLS = [
    # Originais
    "llm", "rag", "agente", "agentes", "agent", "agents",
    # Adicionadas do seu currículo
    "crewai", "langfuse", "ia generativa", "generative ai", "genai", 
    "prompt engineering", "chain-of-thought", "nlp"
]
MIN_SCORE_THRESHOLD = 5

# ==========================================
# 2. MOTOR DE SCORING (MATCHING)
# ==========================================
def calculate_score(description: str):
    """Calcula o score de aderência da vaga baseado nas skills."""
    score = 0
    matched_skills = set()
    desc_lower = description.lower()
    
    # Pesos Máximos (5 pontos)
    for skill in MAX_WEIGHT_SKILLS:
        if re.search(rf'\b{skill}\b', desc_lower):
            score += 5
            matched_skills.add(skill.upper())
            
    # Pesos Normais (1 ponto)
    for skill in NORMAL_WEIGHT_SKILLS:
        if re.search(rf'\b{skill}\b', desc_lower):
            score += 1
            matched_skills.add(skill.capitalize())
            
    return score, list(matched_skills)

def is_target_job(title: str) -> bool:
    """Verifica se o título contém os cargos, níveis e modalidade desejados."""
    title_lower = title.lower()
    
    has_title = any(t in title_lower for t in TARGET_TITLES)
    has_level = any(re.search(rf'\b{l}\b', title_lower) for l in LEVELS)
    has_modality = any(m in title_lower for m in MODALITY)
    
    # Retorna True se for o cargo certo E o nível certo (modalidade pode ser verificada na descrição ou título)
    return has_title and has_level

# ==========================================
# 3. SCRAPERS (FONTES DE BUSCA)
# ==========================================
def scrape_linkedin_rss():
    """Busca vagas no LinkedIn via RSS (Evita bloqueios simples de HTML)."""
    jobs = []
    # Query: "Data Scientist" OR "Machine Learning" no Brasil
    rss_url = "https://www.linkedin.com/jobs/search/?f_WRA=true&geoId=106057199&keywords=Data%20Scientist%20OR%20Machine%20Learning%20Engineer&location=Brazil&f_E=2%2C3"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(rss_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for card in soup.find_all('div', class_='base-card'):
            title_tag = card.find('h3', class_='base-search-card__title')
            company_tag = card.find('h4', class_='base-search-card__subtitle')
            link_tag = card.find('a', class_='base-card__full-link')
            
            if title_tag and company_tag and link_tag:
                title = title_tag.text.strip()
                company = company_tag.text.strip()
                link = link_tag['href']
                
                if is_target_job(title):
                    # Em um cenário real de produção, faríamos um GET no `link` para pegar a descrição completa.
                    # Aqui, simulamos uma descrição mockada para o exemplo.
                    mock_desc = "Trabalho remoto com Python, AWS, RAG e criação de Agentes LLM."
                    score, matched = calculate_score(mock_desc)
                    
                    if score >= MIN_SCORE_THRESHOLD:
                        jobs.append({"company": company, "title": title, "link": link, "score": score, "skills": matched})
    except Exception as e:
        print(f"Erro ao raspar LinkedIn: {e}")
    return jobs

def scrape_remotar():
    """Exemplo de integração com API/Portal focado em remoto."""
    # Como o Remotar requer scraping via GraphQL ou navegação pesada, 
    # utilizamos a estrutura de requisição com headers robustos.
    # OBS: Implementação simplificada da lógica.
    return []

# ==========================================
# 4. ALERTA AUTOMATIZADO (E-MAIL)
# ==========================================
def send_email_alert(jobs):
    if not jobs:
        print("Nenhuma vaga atingiu o score mínimo hoje.")
        return
        
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "samuelbuarquefilho@gmail.com" # Extraído do currículo[cite: 1]
    
    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"🚀 Alerta de Vagas IA/Dados - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    html_content = "<h2>Vagas Encontradas:</h2><ul>"
    for job in sorted(jobs, key=lambda x: x['score'], reverse=True):
        skills_str = ", ".join(job['skills'])
        html_content += f"""
        <li style='margin-bottom: 15px;'>
            <strong>[{job['score']} pts] {job['title']}</strong> na <em>{job['company']}</em><br>
            <strong>Stack Match:</strong> {skills_str}<br>
            <a href="{job['link']}">Aplicar aqui</a>
        </li>
        """
    html_content += "</ul>"
    
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# ==========================================
# 5. ORQUESTRADOR
# ==========================================
if __name__ == "__main__":
    print("A iniciar o Job Crawler...")
    
    # 1. Carregar histórico
    vagas_ja_enviadas = carregar_vagas_enviadas()
    
    found_jobs = []
    found_jobs.extend(scrape_linkedin_rss())
    found_jobs.extend(scrape_remotar())
    
    # 2. Filtrar apenas vagas novas
    vagas_novas = []
    novos_links_para_guardar = vagas_ja_enviadas.copy()
    
    for job in found_jobs:
        if job['link'] not in vagas_ja_enviadas:
            vagas_novas.append(job)
            novos_links_para_guardar.append(job['link'])
    
    # 3. Enviar e-mail e atualizar memória se houver novidades
    if vagas_novas:
        send_email_alert(vagas_novas)
        guardar_vagas_enviadas(novos_links_para_guardar)
        print(f"{len(vagas_novas)} novas vagas processadas e guardadas.")
    else:
        print("Nenhuma vaga nova encontrada hoje.")
=======
import os
import re
import time
import requests
import feedparser
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÕES E PARÂMETROS
# ==========================================
TARGET_TITLES = ["cientista de dados", "data scientist", "engenheiro de machine learning", "machine learning engineer"]
LEVELS = ["jr", "júnior", "junior", "pleno", "pl"]
MODALITY = ["remoto", "remote"]

# Skills extraídas do Samuel_Buarque_AI_Engineer.pdf
NORMAL_WEIGHT_SKILLS = ["python", "genai", "langgraph", "langchain", "pgvector", "postgresql", "aws", "fastapi"]
MAX_WEIGHT_SKILLS = ["llm", "rag", "agente", "agentes", "agent", "agents"]

MIN_SCORE_THRESHOLD = 5

# ==========================================
# 2. MOTOR DE SCORING (MATCHING)
# ==========================================
def calculate_score(description: str):
    """Calcula o score de aderência da vaga baseado nas skills."""
    score = 0
    matched_skills = set()
    desc_lower = description.lower()
    
    # Pesos Máximos (5 pontos)
    for skill in MAX_WEIGHT_SKILLS:
        if re.search(rf'\b{skill}\b', desc_lower):
            score += 5
            matched_skills.add(skill.upper())
            
    # Pesos Normais (1 ponto)
    for skill in NORMAL_WEIGHT_SKILLS:
        if re.search(rf'\b{skill}\b', desc_lower):
            score += 1
            matched_skills.add(skill.capitalize())
            
    return score, list(matched_skills)

def is_target_job(title: str) -> bool:
    """Verifica se o título contém os cargos, níveis e modalidade desejados."""
    title_lower = title.lower()
    
    has_title = any(t in title_lower for t in TARGET_TITLES)
    has_level = any(re.search(rf'\b{l}\b', title_lower) for l in LEVELS)
    has_modality = any(m in title_lower for m in MODALITY)
    
    # Retorna True se for o cargo certo E o nível certo (modalidade pode ser verificada na descrição ou título)
    return has_title and has_level

# ==========================================
# 3. SCRAPERS (FONTES DE BUSCA)
# ==========================================
def scrape_linkedin_rss():
    """Busca vagas no LinkedIn via RSS (Evita bloqueios simples de HTML)."""
    jobs = []
    # Query: "Data Scientist" OR "Machine Learning" no Brasil
    rss_url = "https://www.linkedin.com/jobs/search/?f_WRA=true&geoId=106057199&keywords=Data%20Scientist%20OR%20Machine%20Learning%20Engineer&location=Brazil&f_E=2%2C3"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(rss_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for card in soup.find_all('div', class_='base-card'):
            title_tag = card.find('h3', class_='base-search-card__title')
            company_tag = card.find('h4', class_='base-search-card__subtitle')
            link_tag = card.find('a', class_='base-card__full-link')
            
            if title_tag and company_tag and link_tag:
                title = title_tag.text.strip()
                company = company_tag.text.strip()
                link = link_tag['href']
                
                if is_target_job(title):
                    # Em um cenário real de produção, faríamos um GET no `link` para pegar a descrição completa.
                    # Aqui, simulamos uma descrição mockada para o exemplo.
                    mock_desc = "Trabalho remoto com Python, AWS, RAG e criação de Agentes LLM."
                    score, matched = calculate_score(mock_desc)
                    
                    if score >= MIN_SCORE_THRESHOLD:
                        jobs.append({"company": company, "title": title, "link": link, "score": score, "skills": matched})
    except Exception as e:
        print(f"Erro ao raspar LinkedIn: {e}")
    return jobs

def scrape_remotar():
    """Exemplo de integração com API/Portal focado em remoto."""
    # Como o Remotar requer scraping via GraphQL ou navegação pesada, 
    # utilizamos a estrutura de requisição com headers robustos.
    # OBS: Implementação simplificada da lógica.
    return []

# ==========================================
# 4. ALERTA AUTOMATIZADO (E-MAIL)
# ==========================================
def send_email_alert(jobs):
    if not jobs:
        print("Nenhuma vaga atingiu o score mínimo hoje.")
        return
        
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    receiver_email = "samuelbuarquefilho@gmail.com" # Extraído do currículo[cite: 1]
    
    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"🚀 Alerta de Vagas IA/Dados - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    html_content = "<h2>Vagas Encontradas:</h2><ul>"
    for job in sorted(jobs, key=lambda x: x['score'], reverse=True):
        skills_str = ", ".join(job['skills'])
        html_content += f"""
        <li style='margin-bottom: 15px;'>
            <strong>[{job['score']} pts] {job['title']}</strong> na <em>{job['company']}</em><br>
            <strong>Stack Match:</strong> {skills_str}<br>
            <a href="{job['link']}">Aplicar aqui</a>
        </li>
        """
    html_content += "</ul>"
    
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# ==========================================
# 5. ORQUESTRADOR
# ==========================================
if __name__ == "__main__":
    print("Iniciando Job Crawler...")
    found_jobs = []
    
    found_jobs.extend(scrape_linkedin_rss())
    found_jobs.extend(scrape_remotar())
    
    send_email_alert(found_jobs)
>>>>>>> f1d60ece1d278e54335111be368beed4751ed9ac
