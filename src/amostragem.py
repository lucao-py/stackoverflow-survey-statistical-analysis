
import math


def dimensionar_amostra(df, z=1.96, p=0.50, erro=0.05):
    N = len(df)

    # Dimensionamento inicial
    n0 = (z**2 * p * (1 - p)) / erro**2

    # Correção para população finita
    n_corrigido = (N * n0) / (N + n0 - 1)
    n_final = math.ceil(n_corrigido)

    # Ajuste pela disponibilidade de respostas em AISelect
    taxa_validas = df["AISelect"].notna().mean()

    if taxa_validas == 0:
        raise ValueError("AISelect não possui respostas válidas.")

    n_ajustado = min(N, math.ceil(n_final / taxa_validas))

    return {
        "N": N,
        "n0": n0,
        "n_corrigido": n_corrigido,
        "n_final": n_final,
        "taxa_validas": taxa_validas,
        "n_ajustado": n_ajustado,
    }


def selecionar_amostra(df, tamanho, seed=42):
    return df.sample(
        n=tamanho,
        replace=False,
        random_state=seed
    ).copy()
