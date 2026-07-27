FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY policy-repository ./policy-repository
COPY schemas ./schemas
COPY website ./website
RUN pip install --no-cache-dir .

ENTRYPOINT ["api-standards"]
CMD ["--help"]
