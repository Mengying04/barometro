"""BARómetro: la fecha de hoy, siempre en hora de Madrid.

`date.today()` usa la zona horaria del proceso, y esa zona no es siempre la de Madrid:
Streamlit Community Cloud y GitHub Actions funcionan en UTC, y el cliente MCP arranca el
servidor sin pasarle la variable TZ. Entre las 00:00 y la 01:00 de Madrid (las 02:00 en
verano) la fecha UTC aún es la del día anterior, y los festivos «próximos», sus avisos, la
fecha del informe y el día típico del transporte salían con un día de retraso.

Se usa la base de zonas horarias del sistema y, si no la hay, el paquete `tzdata`
(requirements.txt).
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("Europe/Madrid")


def hoy() -> date:
    """La fecha de hoy en Madrid, sea cual sea la zona horaria del proceso."""
    return datetime.now(ZONA).date()
