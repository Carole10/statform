import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import uuid, os

CHARTS_DIR = "static/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

def generer_stats_completes(df: pd.DataFrame, form_id: uuid.UUID):
    results = {"tables": {}, "charts": {}}
    df_numeric = df.apply(pd.to_numeric, errors='ignore')
    del df['g-recaptcha-response']  # Supprimer la colonne avant les stats
    print(df.describe())
    print(df)

    for col in df.columns:
        if col == "g-recaptcha-response":
            continue
        results["tables"][col] = df[col].value_counts().to_frame('Effectif').to_dict('index')

    for col in df.select_dtypes(include=['object']).columns:
        #print("le colonne  : ", col)
        if col == "g-recaptcha-response":
            continue
        if df[col].nunique() > 20: continue # Pas de camembert si trop de valeurs
        path = f"{CHARTS_DIR}/{form_id}_{col}_pie.png"
        df[col].value_counts().plot.pie(autopct='%1.1f%%', figsize=(6, 6), colors=plt.cm.Pastel1.colors)
        plt.title(f'Répartition - {col}')
        plt.ylabel('')
        plt.savefig(path, bbox_inches='tight', dpi=150)
        plt.close()
        results["charts"][f"pie_{col}"] = path

    numeric_cols = df_numeric.select_dtypes(include=np.number).columns
    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        X = df_numeric[[x_col]].dropna()
        y = df_numeric[y_col].dropna()
        common_idx = X.index.intersection(y.index)
        X, y = X.loc[common_idx], y.loc[common_idx]

        if len(X) > 1:
            path_scatter = f"{CHARTS_DIR}/{form_id}_scatter.png"
            plt.figure(figsize=(8,6))
            plt.scatter(X, y, alpha=0.6)
            model = LinearRegression().fit(X, y)
            plt.plot(X, model.predict(X), color='#FF6B6B', linewidth=2,
                     label=f'Régression: y={model.coef_[0]:.2f}x+{model.intercept_:.2f}')
            plt.xlabel(x_col, fontsize=12)
            plt.ylabel(y_col, fontsize=12)
            plt.title(f'Nuage de points : {y_col} vs {x_col}', fontsize=14, weight='bold')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig(path_scatter, bbox_inches='tight', dpi=150)
            plt.close()
            results["charts"]["scatter_regression"] = path_scatter
            results["regression"] = {"coef": model.coef_[0], "intercept": model.intercept_, "r2": model.score(X, y)}

    return results

