
import math
from scipy.stats import norm, t


def intervalo_proporcao(sucessos, n, N, confianca=0.95):
    proporcao = sucessos / n

    # Valor crítico da distribuição normal
    z = norm.ppf(1 - (1 - confianca) / 2)

    # Correção para população finita
    correcao = math.sqrt((N - n) / (N - 1))

    # Erro-padrão da proporção
    erro_padrao = math.sqrt(
        proporcao * (1 - proporcao) / n
    ) * correcao

    margem = z * erro_padrao

    return {
        "estimativa": proporcao,
        "inferior": max(0, proporcao - margem),
        "superior": min(1, proporcao + margem),
        "n": n
    }


def intervalo_media(valores, N, confianca=0.95):
    valores = valores.dropna()

    n = len(valores)
    media = valores.mean()
    desvio = valores.std(ddof=1)

    # Valor crítico t de Student
    t_critico = t.ppf(
        1 - (1 - confianca) / 2,
        df=n - 1
    )

    # Erro-padrão com correção finita
    correcao = math.sqrt((N - n) / (N - 1))
    erro_padrao = (desvio / math.sqrt(n)) * correcao

    margem = t_critico * erro_padrao

    return {
        "estimativa": media,
        "inferior": media - margem,
        "superior": media + margem,
        "n": n
    }

def teste_proporcao(sucessos, n, N, p0=0.75):
    proporcao = sucessos / n

    erro_padrao = math.sqrt(
        (p0 * (1 - p0) / n) *
        ((N - n) / (N - 1))
    )

    z = (proporcao - p0) / erro_padrao
    valor_p = norm.sf(z)

    return {
        "proporcao": proporcao,
        "z": z,
        "valor_p": valor_p,
        "rejeitar_h0": valor_p < 0.05
    }


def teste_media(valores, N, mu0, alternativa="maior", alfa=0.05):
    valores = valores.dropna()

    n = len(valores)
    media = valores.mean()
    desvio = valores.std(ddof=1)

    # Erro-padrão com correção finita
    erro_padrao = (desvio / math.sqrt(n)) * math.sqrt(
        (N - n) / (N - 1)
    )

    # Estatística do teste
    t_calculado = (media - mu0) / erro_padrao

    # Valor-p conforme a hipótese alternativa
    if alternativa == "maior":
        valor_p = t.sf(t_calculado, df=n - 1)
    elif alternativa == "diferente":
        valor_p = 2 * t.sf(abs(t_calculado), df=n - 1)
    else:
        raise ValueError("Alternativa inválida.")

    return {
        "estimativa": media,
        "t": t_calculado,
        "valor_p": valor_p,
        "rejeitar_h0": valor_p < alfa,
        "n": n
    }
