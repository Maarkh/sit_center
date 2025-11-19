# core/smart_alerts.py
import pandas as pd
from typing import Optional
from core.alert_settings import load_alert_settings_cached, AlertSettings


def check_growth_alert(df: pd.DataFrame, col: str, metric_name: str, alert_settings: AlertSettings) -> Optional[str]:
    """
    Проверяет аномальный рост метрики за короткий период.
    Использует настройки из AlertSettings.
    """
    if alert_settings is None:
        alert_settings = load_alert_settings_cached()
    settings = alert_settings
    if not settings.smart_growth_enabled:
        return None

    # Проверяем, есть ли настройки для этой метрики
    growth_config = settings.smart_growth.get(col)
    if not growth_config or df.empty or col not in df.columns:
        return None

    percent_threshold = growth_config.get("percent", 50)
    period_minutes = growth_config.get("period_minutes", 60)

    # Фильтруем данные за период
    cutoff = pd.Timestamp.now(tz=df["timestamp"].iloc[0].tz) - pd.Timedelta(minutes=period_minutes)
    recent_df = df[df["timestamp"] >= cutoff]

    if recent_df.empty or len(recent_df) < 2:
        return None

    # Группируем по регионам
    latest = recent_df.groupby("region").last()
    earliest = recent_df.groupby("region").first()

    # Вычисляем рост
    for region in latest.index:
        if region not in earliest.index:
            continue

        old_val = earliest.loc[region, col]
        new_val = latest.loc[region, col]

        if old_val == 0:
            if new_val > 0: # type: ignore
                growth_percent = 100.0
            else:
                continue
        else:
            growth_percent = ((new_val - old_val) / old_val) * 100 # type: ignore

        if growth_percent >= percent_threshold: # type: ignore
            return f"📈 Рост {metric_name}: +{growth_percent:.1f}% в регионе {region} за {period_minutes} мин"

    return None


def check_deviation_alert(df: pd.DataFrame, col: str, metric_name: str, alert_settings: AlertSettings) -> Optional[str]:
    """
    Проверяет отклонение от среднего (в std).
    """
    if alert_settings is None:
        alert_settings = load_alert_settings_cached()
    settings = alert_settings
    if not settings.smart_deviation_enabled:
        return None

    deviation_config = settings.smart_deviation.get(col)
    if not deviation_config or df.empty or col not in df.columns:
        return None

    std_threshold = deviation_config.get("std_dev", 2.0)

    values = df[col].dropna()
    if len(values) < 2:
        return None

    mean_val = values.mean()
    std_val = values.std()

    if std_val == 0:
        return None

    for _, row in df.iterrows():
        z_score = (row[col] - mean_val) / std_val
        if z_score > std_threshold:
            return f"⚠️ Отклонение {metric_name}: {row[col]} в {row['region']} (z={z_score:.2f})"

    return None