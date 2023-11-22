FROM mcr.microsoft.com/azureml/minimal-ubuntu20.04-py38-cpu-inference:latest

# Ensure terminal output is sent directly to logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
# To prep the wheel file, run:
# pushd ../model
# python setup.py sdist bdist_wheel
# cp dist/t4t_headstamp-0.0.3-py3-none-any.whl ../annotation
# popd
ARG T4T_WHL=t4t_headstamp-0.0.3-py3-none-any.whl


# Install requirements
# TODO: separate development from production requirements (and Dockerfiles)
COPY ./requirements.txt /requirements.txt
COPY ./${T4T_WHL} /${T4T_WHL}
RUN pip install --upgrade pip
RUN pip install -r /requirements.txt
RUN pip install /${T4T_WHL}

ADD . /app
WORKDIR /app

EXPOSE 8080

CMD ./devops/run-annotation-api-local.sh