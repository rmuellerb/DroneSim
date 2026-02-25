FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Non-root user/group (predictable IDs)
RUN addgroup --system --gid 10001 app \
 && adduser  --system --uid 10001 --ingroup app app

COPY ./entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//g' /app/entrypoint.sh \
 && chmod +x /app/entrypoint.sh

COPY . /app/

# Writable dirs for collectstatic/logging
RUN mkdir -p /app/staticfiles /var/log/dronesim \
 && chown -R app:app /app /var/log/dronesim

USER 10001:10001

ENTRYPOINT ["/app/entrypoint.sh"]
