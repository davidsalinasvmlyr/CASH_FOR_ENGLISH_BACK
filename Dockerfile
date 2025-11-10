# ==============================================================================
# Base Image - Python 3.11 slim
# ==============================================================================
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y habilitar output sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# ==============================================================================
# Instalar dependencias del sistema
# ==============================================================================
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Instalar dependencias Python
# ==============================================================================
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Copiar código del proyecto
# ==============================================================================
COPY . /app/

# ==============================================================================
# Crear usuario no-root para ejecutar la aplicación (buena práctica de seguridad)
# ==============================================================================
RUN addgroup --system django && \
    adduser --system --ingroup django django

# Cambiar permisos
RUN chown -R django:django /app

# Cambiar a usuario no-root
USER django

# ==============================================================================
# Exponer puerto
# ==============================================================================
EXPOSE 8000

# Comando por defecto (puede ser sobrescrito en docker-compose)
CMD ["gunicorn", "cash_for_english.wsgi:application", "--bind", "0.0.0.0:8000"]
