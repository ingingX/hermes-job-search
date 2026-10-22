FROM oven/bun@sha256:923bedb355f7746666659f71e724998159a5c8c54bd1cb1030e1975a0698415b AS bun
FROM nousresearch/hermes-agent@sha256:99641e57ec762c59e54cb44aa6746b7fc68c18b3c5ddb088af54234c613d9294

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -o Acquire::Retries=3 update && \
    apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
      texlive-luatex texlive-xetex texlive-latex-extra texlive-fonts-extra \
      texlive-fonts-recommended poppler-utils && \
    rm -rf /var/lib/apt/lists/*
COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun
RUN bun --version
