FROM python:3.15.0-slim-trixie AS base
WORKDIR /app

#Build stage 
FROM base AS builder
#Install uv without cache 
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential=12.12 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.12.15

COPY ./backend/pyproject.toml ./backend/uv.lock /app/
RUN uv sync --locked --no-install-project --python /usr/local/bin/python --no-python-downloads

COPY ./backend /app
RUN uv sync --locked --python /usr/local/bin/python --no-python-downloads

#Run stage 
FROM base AS runtime
#Create user as to not run as root
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin app

#Copying over nessicary files from builder stage 
COPY --from=builder --chown=10001:10001 /app/pyproject.toml /app/pyproject.toml
COPY --from=builder --chown=10001:10001 /app/src /app/src
COPY --from=builder --chown=10001:10001 /app/.venv /app/.venv

# Add the virtual environment executables to PATH.
ENV PATH="/app/.venv/bin:${PATH}"
USER 10001:10001

RUN DATABASE_URL=sqlite:// fastapi --help >/dev/null \
    && DATABASE_URL=sqlite:// python -c "from bc_ferry_data_platform.main import app; assert app"

EXPOSE 8000

ENTRYPOINT ["fastapi"]
CMD ["run", "--host", "0.0.0.0", "--port", "8000"]
