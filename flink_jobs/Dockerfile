FROM flink:1.17.1-python3.9
WORKDIR /opt/flink/app
COPY solar_forecast.py /opt/flink/app/
RUN pip install --no-cache-dir pandas prophet pyflink
CMD ["python", "solar_forecast.py"]
