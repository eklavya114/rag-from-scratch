# This file is written for reading, it is not built or run in any test
# in this project. It describes how api_server.py COULD be packaged
# into a container for a real deployment.

# A slim base image: the full Python image includes build tools and
# libraries most services never need, the slim variant keeps the image
# smaller and with a reduced attack surface.
FROM python:3.12-slim

# Everything below happens inside this directory in the image.
WORKDIR /app

# Copy this folder's code, plus Day 22's RagService it depends on, into
# the image. A real multi-folder project would more likely package Day
# 22 as an installable dependency rather than copying its source
# directly, this mirrors how the two folders are wired together in this
# project today.
COPY day-23-deployment/ /app/day-23-deployment/
COPY day-22-production-rag/ /app/day-22-production-rag/

WORKDIR /app/day-23-deployment

# Every file in this project uses only the Python standard library, so
# there is nothing to install here, no requirements.txt and no pip
# install step. A real service with third-party dependencies would add
# a COPY requirements.txt and a RUN pip install step here, before
# copying the rest of the source, so Docker can cache that layer
# separately from code changes.

# Document which port the server listens on. EXPOSE is metadata, it does
# not actually publish the port, running the container still needs
# `-p HOST_PORT:8000` to make it reachable from outside the container.
EXPOSE 8000

# The port the server listens on inside the container, read by
# api_server.py's main() via os.environ.get("RAG_API_PORT", "8000").
ENV RAG_API_PORT=8000

# Start the real, permanently-listening server, the same run_server()
# entry point used outside of Docker.
CMD ["python", "api_server.py"]
