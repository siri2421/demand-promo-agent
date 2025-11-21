FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY app.py .
EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]