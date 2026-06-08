FROM public.ecr.aws/lambda/python:3.12

ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0
ENV PYTHONUNBUFFERED=1

RUN dnf install -y \
    atk \
    at-spi2-atk \
    cups-libs \
    dbus-libs \
    libdrm \
    libX11 \
    libXcomposite \
    libXdamage \
    libXext \
    libXfixes \
    libXrandr \
    libxcb \
    libxkbcommon \
    mesa-libgbm \
    nss \
    pango \
    alsa-lib \
    && dnf clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt \
    && mkdir -p ${PLAYWRIGHT_BROWSERS_PATH} \
    && playwright install chromium

COPY app ${LAMBDA_TASK_ROOT}/app

CMD ["app.main.handler"]
