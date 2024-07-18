FROM ubuntu:22.04

# Install Python
RUN apt-get -y update && \
    apt-get install -y python3-pip

# Set the current working directory
WORKDIR /ML-SOC-API

# Copy project files to the image
COPY --chown=${USERNAME}:${GROUPNAME} . .

# Install all the requirements
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH="/ML-SOC-API/app:${PYTHONPATH}"

# Launch the unicorn server to run the API
EXPOSE 5000
CMD ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "5000"]
