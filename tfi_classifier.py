# -*- coding: utf-8 -*-
"""
tfi_classifier.py — Classificador de documentos por TF-IDF
EVT Analytica — Módulo de categorização automática

Categorias disponíveis:
  HVAC · Elétrica · Hidráulica · Segurança
  Manutenção · Relatório · Projeto

Pipeline:
  1. Extrair texto de PDF / DOCX / TXT
  2. Vetorizar com TfidfVectorizer (sklearn)
  3. Classificar via similaridade cosseno contra corpus de treino
"""

import os
import logging

logger = logging.getLogger(__name__)

# =====================================================================
# Corpus de treino — frases representativas por categoria
# =====================================================================
TRAINING_DATA = {
    "HVAC": [
        "ar condicionado central não está refrigerando",
        "chiller com defeito na torre de resfriamento",
        "climatização do andar está fora do setpoint",
        "temperatura ambiente acima do normal",
        "ventilação mecânica do subsolo parou",
        "duto de insuflamento com obstrução",
        "fan coil apresentando vazamento de água gelada",
        "condensadora com alta pressão no compressor",
        "evaporadora com gelo na serpentina",
        "refrigeração da sala de servidores em falha",
        "sistema de exaustão não funciona corretamente",
        "troca de filtro do ar condicionado preventiva",
        "setpoint de temperatura ajustado para 23 graus",
        "válvula de expansão do chiller com defeito",
        "bomba de água gelada com vibração excessiva",
    ],
    "Elétrica": [
        "elétrica geral do prédio com oscilação",
        "disjuntor do quadro principal desarmou",
        "transformador de 500 kVA com aquecimento",
        "circuito do andar 15 sobrecarregado",
        "quadro elétrico de distribuição precisa revisão",
        "cabeamento estruturado da rede elétrica",
        "energia do gerador de emergência falhou no teste",
        "gerador diesel não partiu no último blackout",
        "nobreak da sala de TI com bateria fraca",
        "curto circuito identificado na subestação",
        "medição de energia para faturamento da concessionária",
        "troca de lâmpadas LED no estacionamento",
        "quadro de automação elétrica com alarme",
    ],
    "Hidráulica": [
        "hidráulica do banheiro do 5 andar com problemas",
        "bomba de recalque não está funcionando",
        "tubulação de água fria com vazamento",
        "válvula de retenção travada na posição aberta",
        "pressão da rede hidráulica abaixo do normal",
        "vazamento na junta de dilatação do 12 andar",
        "esgoto entupido no subsolo 2",
        "água gelada com perda de carga excessiva",
        "torre de resfriamento com incrustação nos bicos",
        "bomba centrífuga com selo mecânico danificado",
        "reservatório superior precisa de limpeza semestral",
        "sistema de reúso de água da chuva parado",
        "hidrante do 8 andar sem pressão adequada",
    ],
    "Segurança": [
        "segurança patrimonial reportou acesso não autorizado",
        "câmera do lobby principal está offline",
        "CFTV do estacionamento sem gravação há 2 dias",
        "alarme de intrusão disparou na sala técnica",
        "controle de acesso do catracas não reconhece crachá",
        "incêndio simulado programado para próxima semana",
        "detector de fumaça do corredor está piscando",
        "sprinkler do depósito foi acionado acidentalmente",
        "extintores do 3 andar vencem este mês",
        "central de alarme de incêndio com falha de zona",
        "porta corta fogo do 10 andar não fecha corretamente",
        "brigada de incêndio precisa de treinamento anual",
    ],
    "Manutenção": [
        "manutenção preventiva mensal dos equipamentos HVAC",
        "preventiva das bombas de recalque agendada",
        "corretiva emergencial no elevador social",
        "preditiva por análise de vibração no motor",
        "inspeção trimestral dos quadros elétricos",
        "checklist de manutenção predial semanal",
        "ordem de serviço aberta para reparo no telhado",
        "manutenção programada do gerador diesel",
        "lubrificação dos rolamentos das bombas centrífugas",
        "substituição de correia do ventilador de exaustão",
        "calibração dos sensores de temperatura dos andares",
    ],
    "Relatório": [
        "relatório mensal de consumo energético",
        "análise de eficiência dos chillers no trimestre",
        "indicadores de desempenho operacional KPI",
        "KPI de disponibilidade dos sistemas críticos",
        "desempenho da equipe de manutenção no mês",
        "produtividade medida por ordens concluídas",
        "eficiência energética comparada ao ano anterior",
        "relatório de ocorrências e incidentes do mês",
        "dashboard de consumo de água e energia",
        "benchmark de custo operacional por metro quadrado",
    ],
    "Projeto": [
        "projeto de melhoria do sistema de automação predial",
        "melhoria na eficiência do sistema de climatização",
        "implantação do novo sistema BMS em todos os andares",
        "modernização dos elevadores sociais e de serviço",
        "retrofit das luminárias fluorescentes para LED",
        "automação das bombas de incêndio com CLP",
        "integração do CFTV com controle de acesso biométrico",
        "projeto executivo para ampliação da subestação",
        "estudo de viabilidade para cogeração de energia",
        "proposta de instalação de painéis fotovoltaicos",
    ],
}


def _get_vectorizer_and_matrix():
    """
    Cria e retorna o vetorizador TF-IDF treinado e a matriz
    de termos do corpus de referência.

    Retorna
    -------
    tuple (vectorizer, tfidf_matrix, labels)
        vectorizer     — TfidfVectorizer treinado
        tfidf_matrix   — Sparse matrix do corpus
        labels         — Lista de categorias alinhadas às linhas
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        raise ImportError(
            "scikit-learn é necessário. Instale com: pip install scikit-learn"
        )

    corpus = []
    labels = []
    for category, phrases in TRAINING_DATA.items():
        for phrase in phrases:
            corpus.append(phrase)
            labels.append(category)

    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents='unicode',
        ngram_range=(1, 2),      # Unigramas e bigramas
        max_features=5000,
        sublinear_tf=True,       # Suaviza frequências altas
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)

    return vectorizer, tfidf_matrix, labels


# =====================================================================
# Cache do modelo (inicializado na primeira chamada)
# =====================================================================
_cached_model = None


def _get_model():
    """Retorna modelo cacheado (lazy loading)."""
    global _cached_model
    if _cached_model is None:
        _cached_model = _get_vectorizer_and_matrix()
    return _cached_model


# =====================================================================
# Extração de texto de arquivos
# =====================================================================
def extract_text_from_file(filepath: str) -> str:
    """
    Extrai texto de um arquivo nos formatos PDF, DOCX ou TXT.

    Parâmetros
    ----------
    filepath : str
        Caminho absoluto ou relativo do arquivo.

    Retorna
    -------
    str — Texto extraído (vazio se formato não suportado ou erro).
    """
    if not os.path.isfile(filepath):
        logger.warning(f"Arquivo não encontrado: {filepath}")
        return ""

    ext = os.path.splitext(filepath)[1].lower()

    # --- PDF ---
    if ext == '.pdf':
        return _extract_pdf(filepath)

    # --- DOCX ---
    if ext == '.docx':
        return _extract_docx(filepath)

    # --- TXT / CSV / LOG ---
    if ext in ('.txt', '.csv', '.log', '.md'):
        return _extract_text(filepath)

    logger.info(f"Formato não suportado para extração: {ext}")
    return ""


def _extract_pdf(filepath: str) -> str:
    """Extrai texto de PDF usando PyPDF2."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        logger.error("PyPDF2 não instalado. Use: pip install PyPDF2")
        return ""

    try:
        reader = PdfReader(filepath)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n".join(pages_text)
    except Exception as e:
        logger.error(f"Erro ao ler PDF {filepath}: {e}")
        return ""


def _extract_docx(filepath: str) -> str:
    """Extrai texto de DOCX usando python-docx."""
    try:
        from docx import Document
    except ImportError:
        logger.error("python-docx não instalado. Use: pip install python-docx")
        return ""

    try:
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"Erro ao ler DOCX {filepath}: {e}")
        return ""


def _extract_text(filepath: str) -> str:
    """Lê arquivo de texto puro (UTF-8 com fallback para latin-1)."""
    for encoding in ('utf-8', 'latin-1', 'cp1252'):
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            logger.error(f"Erro ao ler {filepath}: {e}")
            return ""
    return ""


# =====================================================================
# Classificação
# =====================================================================
def classify_document(text: str) -> tuple:
    """
    Classifica um texto em uma das categorias predefinidas.

    Utiliza TF-IDF + similaridade cosseno contra o corpus de
    frases de treino.

    Parâmetros
    ----------
    text : str
        Texto a ser classificado.

    Retorna
    -------
    tuple (categoria: str, confiança: float)
        Ex.: (``'HVAC'``, ``0.72``)
        Se o texto estiver vazio, retorna (``'Indefinido'``, ``0.0``).
    """
    if not text or not text.strip():
        return ("Indefinido", 0.0)

    try:
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        raise ImportError(
            "scikit-learn é necessário. Instale com: pip install scikit-learn"
        )

    vectorizer, tfidf_matrix, labels = _get_model()

    # Vetorizar o documento de entrada
    doc_vector = vectorizer.transform([text])

    # Calcular similaridade com todo o corpus
    similarities = cosine_similarity(doc_vector, tfidf_matrix).flatten()

    # Agregar scores por categoria (média das Top-N maiores similaridades)
    from collections import defaultdict
    category_scores = defaultdict(list)
    for score, label in zip(similarities, labels):
        category_scores[label].append(score)

    # Usar média das top-3 similaridades por categoria
    category_avg = {}
    for cat, scores in category_scores.items():
        top_scores = sorted(scores, reverse=True)[:3]
        category_avg[cat] = sum(top_scores) / len(top_scores)

    # Melhor categoria
    best_category = max(category_avg, key=category_avg.get)
    best_score = round(category_avg[best_category], 4)

    return (best_category, best_score)


def classify_uploaded_file(filepath: str, user_comment: str = '') -> tuple:
    """
    Classifica um arquivo enviado pelo usuário.

    Combina o texto extraído do arquivo com um comentário opcional
    do usuário para melhorar a classificação.

    Parâmetros
    ----------
    filepath : str
        Caminho do arquivo (PDF, DOCX ou TXT).
    user_comment : str
        Comentário adicional do usuário sobre o documento.

    Retorna
    -------
    tuple (categoria: str, confiança: float)
    """
    # Extrair texto do arquivo
    file_text = extract_text_from_file(filepath)

    # Combinar com comentário do usuário (peso maior ao comentário)
    combined = ""
    if user_comment:
        # Repetir comentário para dar mais peso
        combined = (user_comment + " ") * 3
    if file_text:
        # Usar no máximo primeiros 5000 caracteres do arquivo
        combined += file_text[:5000]

    if not combined.strip():
        logger.warning(f"Nenhum texto extraído de {filepath}")
        return ("Indefinido", 0.0)

    return classify_document(combined)


# =====================================================================
# Execução direta para testes rápidos
# =====================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  TESTE — tfi_classifier.py")
    print("=" * 60)

    # Textos de teste
    testes = [
        "O chiller do 10 andar está com temperatura alta e o fan coil não refrigera.",
        "Preciso do relatório mensal de indicadores de eficiência energética.",
        "Disjuntor do quadro geral desarmou e o nobreak assumiu a carga.",
        "Câmera do CFTV do estacionamento parou de gravar ontem à noite.",
        "Bomba de recalque com vazamento na tubulação de água fria.",
        "Manutenção preventiva trimestral dos elevadores programada.",
        "Projeto de retrofit da iluminação do estacionamento para LED.",
    ]

    for texto in testes:
        cat, score = classify_document(texto)
        print(f"\n  Texto : {texto[:70]}...")
        print(f"  Classe: {cat} (confiança: {score:.2%})")
