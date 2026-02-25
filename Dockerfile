FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV HOME=/app
WORKDIR $HOME

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY ./entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//g' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

COPY . /app/

# Non-root user
RUN useradd -m -u 10001 appuser \
  && mkdir -p /app/staticfiles /var/log/dronesim \
  && chown -R appuser:appuser /app /var/log/dronesim

USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]
