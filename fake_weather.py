# -*- coding: utf-8 -*-
"""
fake_weather.py — Módulo de simulação de APIs externas (clima e notícias)
EVT Analytica — Dados fictícios para demonstração

Simula chamadas a:
  • OpenWeatherMap API  → get_weather()
  • API de notícias     → get_news()
  • Scraping Climatempo → scrape_climatempo()

Todas as respostas são geradas localmente com variação realista
baseada na hora do dia e em aleatoriedade controlada.
"""

import random
import math
from datetime import datetime, timedelta
import json
import os


# =====================================================================
# Constantes geográficas (São Paulo, SP)
# =====================================================================
_SP_LON = -46.6361
_SP_LAT = -23.5475

# =====================================================================
# Descrições de clima — mapeadas ao formato da OpenWeather API
# =====================================================================
_WEATHER_CONDITIONS = [
    {"id": 800, "main": "Clear",  "description": "céu limpo",           "icon": "01d"},
    {"id": 801, "main": "Clouds", "description": "poucas nuvens",       "icon": "02d"},
    {"id": 802, "main": "Clouds", "description": "nublado",             "icon": "04d"},
    {"id": 803, "main": "Clouds", "description": "parcialmente nublado","icon": "03d"},
    {"id": 500, "main": "Rain",   "description": "chuva leve",          "icon": "10d"},
    {"id": 501, "main": "Rain",   "description": "chuva moderada",      "icon": "10d"},
    {"id": 502, "main": "Rain",   "description": "chuva forte",         "icon": "09d"},
    {"id": 211, "main": "Thunderstorm", "description": "trovoada",      "icon": "11d"},
]


def _diurnal_temp(hour: int) -> float:
    """
    Retorna temperatura-base (°C) com variação senoidal ao longo do dia.
    Mínima ~18 °C às 05h, máxima ~32 °C às 15h.
    """
    # Fase deslocada para pico às 15h (hora = 15 → ângulo = π/2)
    angle = math.pi * (hour - 9) / 12.0
    base = 25.0  # média diurna de São Paulo
    amplitude = 7.0
    return base + amplitude * math.sin(angle)


def get_weather(city: str = 'São Paulo,BR') -> dict:
    """
    Simula resposta da OpenWeatherMap Current Weather API.

    Retorna dict no formato idêntico ao JSON da API real,
    com temperatura variando de acordo com a hora atual.

    Parâmetros
    ----------
    city : str
        Nome da cidade (ignorado para cálculo, mas incluído na resposta).

    Retorna
    -------
    dict  — Estrutura compatível com OpenWeather ``/data/2.5/weather``.
    """
    now = datetime.now()
    hour = now.hour

    # Temperatura com variação diurna + ruído aleatório (±1.5 °C)
    temp_base = _diurnal_temp(hour)
    noise = random.uniform(-1.5, 1.5)
    temp = round(temp_base + noise, 1)
    feels_like = round(temp + random.uniform(-0.5, 1.5), 1)
    temp_min = round(temp - random.uniform(2.0, 4.0), 1)
    temp_max = round(temp + random.uniform(2.0, 5.0), 1)

    # Umidade: maior à noite e de manhã
    if 0 <= hour < 6:
        humidity = random.randint(70, 95)
    elif 6 <= hour < 12:
        humidity = random.randint(55, 80)
    elif 12 <= hour < 18:
        humidity = random.randint(40, 65)
    else:
        humidity = random.randint(55, 80)

    # Condição climática — pesos diferentes por período
    if 12 <= hour < 18:
        # Tarde: mais chance de chuva/trovoada em SP
        weights = [10, 15, 20, 15, 15, 10, 8, 7]
    elif 0 <= hour < 6:
        # Madrugada: geralmente limpo ou nublado
        weights = [25, 20, 20, 15, 10, 5, 3, 2]
    else:
        weights = [15, 20, 20, 20, 10, 8, 5, 2]

    condition = random.choices(_WEATHER_CONDITIONS, weights=weights, k=1)[0]

    # Ajustar ícone para noite (sufixo 'n' entre 18h e 6h)
    icon = condition["icon"]
    if hour >= 18 or hour < 6:
        icon = icon.replace("d", "n")

    # Vento
    wind_speed = round(random.uniform(1.0, 8.0), 1)
    wind_deg = random.randint(0, 359)

    # Pressão atmosférica típica de SP (~925 hPa pela altitude)
    pressure = random.randint(920, 935)

    return {
        "coord": {"lon": _SP_LON, "lat": _SP_LAT},
        "weather": [{
            "id": condition["id"],
            "main": condition["main"],
            "description": condition["description"],
            "icon": icon,
        }],
        "base": "stations",
        "main": {
            "temp": temp,
            "feels_like": feels_like,
            "temp_min": temp_min,
            "temp_max": temp_max,
            "pressure": pressure,
            "humidity": humidity,
        },
        "visibility": random.randint(6000, 10000),
        "wind": {"speed": wind_speed, "deg": wind_deg},
        "clouds": {"all": random.randint(0, 100)},
        "dt": int(now.timestamp()),
        "sys": {
            "type": 2,
            "id": 8394,
            "country": "BR",
            "sunrise": int(now.replace(hour=6, minute=15, second=0).timestamp()),
            "sunset": int(now.replace(hour=17, minute=45, second=0).timestamp()),
        },
        "timezone": -10800,
        "id": 3448439,
        "name": city.split(",")[0] if "," in city else city,
        "cod": 200,
    }


def get_fake_weather(city: str = "Sao Paulo,BR") -> dict:
    """Alias requested by the demo specification."""
    return get_weather(city)


# =====================================================================
# Banco de manchetes fictícias em português (clima / SP)
# =====================================================================
_HEADLINES = [
    {
        "title": "Frente fria traz chuvas para a Grande São Paulo nesta semana",
        "description": "Meteorologistas alertam para possibilidade de temporal com ventos de até 70 km/h nas próximas 48 horas.",
    },
    {
        "title": "Onda de calor: São Paulo registra 35 °C e bate recorde do mês",
        "description": "Temperaturas acima da média preocupam especialistas; Defesa Civil emite alerta de hidratação.",
    },
    {
        "title": "Chuvas intensas causam alagamentos em vias da Zona Leste",
        "description": "Córrego Aricanduva transbordou na madrugada; trânsito ficou parado por mais de duas horas.",
    },
    {
        "title": "Previsão indica retorno do frio a São Paulo no fim de semana",
        "description": "Massa de ar polar deve derrubar temperaturas para mínima de 12 °C na capital paulista.",
    },
    {
        "title": "Qualidade do ar em SP atinge nível 'muito ruim' pelo terceiro dia",
        "description": "CETESB recomenda evitar exercícios físicos ao ar livre até melhora das condições.",
    },
    {
        "title": "Defesa Civil alerta para risco de deslizamentos em áreas de encosta",
        "description": "Acumulado de chuva em 72 horas supera 100 mm em diversas regiões da cidade.",
    },
    {
        "title": "Climatologistas preveem verão mais chuvoso que a média em 2026",
        "description": "Fenômeno La Niña contribui para aumento de precipitação na região Sudeste.",
    },
    {
        "title": "Rodízio de água pode voltar se estiagem prolongada persistir",
        "description": "Nível do Sistema Cantareira caiu 5 pontos percentuais em duas semanas.",
    },
    {
        "title": "Temperatura da água do mar em Santos bate recorde de 28 °C",
        "description": "Litoral paulista registra valores atípicos; biólogos monitoram impacto na fauna marinha.",
    },
    {
        "title": "Granizo atinge bairros da Zona Norte e danifica veículos",
        "description": "Pedras de gelo de até 3 cm foram registradas em Santana e Tucuruvi.",
    },
    {
        "title": "Inversão térmica deixa São Paulo coberta por névoa seca",
        "description": "Fenômeno meteorológico aprisiona poluentes e reduz visibilidade para menos de 2 km.",
    },
    {
        "title": "Primavera começa com temperaturas amenas e céu limpo na capital",
        "description": "Previsão indica semana estável com máximas de 26 °C e mínimas de 16 °C.",
    },
    {
        "title": "Sistema de monitoramento de enchentes ganha novas estações em SP",
        "description": "Prefeitura instalou 15 sensores hidrológicos em córregos e rios da zona sul.",
    },
    {
        "title": "Vento forte derruba árvores e causa queda de energia em Pinheiros",
        "description": "Enel reportou mais de 50 mil imóveis sem energia na região oeste da capital.",
    },
    {
        "title": "Estudo aponta aumento de 1,2 °C na temperatura média de SP em 30 anos",
        "description": "Pesquisa da USP relaciona aquecimento à expansão urbana e redução de áreas verdes.",
    },
    {
        "title": "Umidade do ar cai abaixo de 20% e SP entra em estado de atenção",
        "description": "OMS recomenda mínimo de 60%; população deve redobrar cuidados com hidratação.",
    },
    {
        "title": "Temporal provoca queda de muro em escola na Zona Sul de SP",
        "description": "Ninguém ficou ferido; aulas foram suspensas por precaução até vistoria estrutural.",
    },
    {
        "title": "Neblina fecha aeroporto de Congonhas por três horas na manhã de hoje",
        "description": "Pelo menos 40 voos foram atrasados ou redirecionados para Guarulhos.",
    },
]

# Fontes fictícias para as notícias
_SOURCES = [
    "Climatempo", "G1 São Paulo", "Folha de S.Paulo",
    "Estadão", "UOL Notícias", "Band News", "CNN Brasil",
    "Jornal Nacional", "R7 Notícias",
]


def get_news(count: int = 10) -> list:
    """
    Retorna lista de notícias fictícias sobre clima em São Paulo.

    Formato compatível com a NewsAPI (``/v2/top-headlines``).

    Parâmetros
    ----------
    count : int
        Quantidade de notícias a retornar (máx = len de _HEADLINES).

    Retorna
    -------
    list[dict]  — Cada dict contém title, description, url, publishedAt, source.
    """
    fake_news_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "news_fake.json")
    if os.path.exists(fake_news_path):
        try:
            with open(fake_news_path, "r", encoding="utf-8") as fh:
                items = json.load(fh)
            now = datetime.now()
            return [
                {
                    "title": item.get("title", "Noticia climatica"),
                    "description": item.get("summary", item.get("description", "")),
                    "url": "#",
                    "publishedAt": (now - timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "source": {"name": "Analytica Demo"},
                }
                for i, item in enumerate(items[:count])
            ]
        except Exception:
            pass

    now = datetime.now()
    selected = random.sample(_HEADLINES, min(count, len(_HEADLINES)))
    news = []

    for i, item in enumerate(selected):
        # Datas publicação espalhadas nos últimos 7 dias
        pub_date = now - timedelta(
            days=random.randint(0, 6),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        news.append({
            "title": item["title"],
            "description": item["description"],
            "url": "#",
            "publishedAt": pub_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source": {"name": random.choice(_SOURCES)},
        })

    # Ordenar por data de publicação (mais recente primeiro)
    news.sort(key=lambda x: x["publishedAt"], reverse=True)
    return news


# =====================================================================
# Simulação de scraping do Climatempo
# =====================================================================
_CLIMATEMPO_ITEMS = [
    {
        "titulo": "Previsão para São Paulo: pancadas de chuva à tarde",
        "resumo": "A instabilidade atmosférica favorece a formação de nuvens carregadas no período da tarde na capital.",
    },
    {
        "titulo": "Fim de semana terá sol entre nuvens e calor em SP",
        "resumo": "Massa de ar quente mantém temperaturas elevadas; máxima pode chegar a 33 °C.",
    },
    {
        "titulo": "Alerta: temporais com raios previstos para a RMSP",
        "resumo": "Modelos meteorológicos indicam risco de descargas elétricas e granizo isolado.",
    },
    {
        "titulo": "Madrugada gelada: termômetros marcam 10 °C em São Paulo",
        "resumo": "Ar frio de origem polar atinge o Sudeste e derruba temperaturas na capital.",
    },
    {
        "titulo": "Semana começa com tempo firme e sem previsão de chuva",
        "resumo": "Bloqueio atmosférico impede avanço de frentes frias até quarta-feira.",
    },
    {
        "titulo": "Umidade relativa do ar em queda: atenção à saúde respiratória",
        "resumo": "Índices abaixo de 30% esperados para os próximos três dias em SP.",
    },
    {
        "titulo": "Primavera traz aumento das chuvas e temperaturas em São Paulo",
        "resumo": "Estação é marcada por temporais frequentes e calor crescente na região metropolitana.",
    },
    {
        "titulo": "Volume de chuva em maio supera média histórica em SP",
        "resumo": "Acumulado já é 40% acima da média climatológica para o mês na capital.",
    },
    {
        "titulo": "Ciclone extratropical pode influenciar o tempo em SP nesta semana",
        "resumo": "Sistema se forma no oceano Atlântico e pode trazer ventos fortes ao litoral paulista.",
    },
    {
        "titulo": "Noite de Natal terá tempo abafado com chance de chuva em SP",
        "resumo": "Combinação de calor e umidade favorece formação de temporais na véspera.",
    },
    {
        "titulo": "El Niño perde força, mas ainda impacta o clima paulistano",
        "resumo": "Transição para fase neutra deve ocorrer nos próximos meses, segundo o INMET.",
    },
    {
        "titulo": "Recorde: São Paulo registra 23 dias consecutivos sem chuva",
        "resumo": "Seca prolongada afeta reservatórios e aumenta risco de incêndios florestais.",
    },
]


def scrape_climatempo() -> list:
    """
    Simula scraping de notícias do site Climatempo.

    Retorna
    -------
    list[dict]  — Cada dict contém titulo, resumo e link.
    """
    items = random.sample(
        _CLIMATEMPO_ITEMS, min(10, len(_CLIMATEMPO_ITEMS))
    )
    return [
        {"titulo": it["titulo"], "resumo": it["resumo"], "link": "#"}
        for it in items
    ]


# =====================================================================
# Execução direta para testes rápidos
# =====================================================================
if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  TESTE — fake_weather.py")
    print("=" * 60)

    print("\n>>> get_weather():")
    print(json.dumps(get_weather(), indent=2, ensure_ascii=False))

    print("\n>>> get_news(5):")
    for n in get_news(5):
        print(f"  • [{n['source']['name']}] {n['title']}")

    print("\n>>> scrape_climatempo():")
    for c in scrape_climatempo():
        print(f"  • {c['titulo']}")
