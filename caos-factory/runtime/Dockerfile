FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl git build-essential pkg-config libssl-dev clang jq && rm -rf /var/lib/apt/lists/*
ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo
RUN curl --proto '=https' --tlsv1.2 -fsS https://sh.rustup.rs -o /tmp/rustup.sh && sh /tmp/rustup.sh -y --profile minimal --default-toolchain nightly-2026-04-19 && rm /tmp/rustup.sh
ENV PATH=/opt/cargo/bin:/usr/local/bin:/usr/bin:/bin CARGO_BUILD_JOBS=2 CARGO_PROFILE_DEV_DEBUG=0 CARGO_PROFILE_TEST_DEBUG=0 CARGO_INCREMENTAL=0 PYTHONDONTWRITEBYTECODE=1
RUN chmod -R a+rX /opt/rustup /opt/cargo
COPY caos /bin/caos
RUN chown root:root /bin/caos && chmod 4755 /bin/caos
COPY worker /worker
RUN chmod 755 /worker
