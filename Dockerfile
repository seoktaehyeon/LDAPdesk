FROM bxwill/ldapdesk:base
LABEL maintainer="v.stone@163.com"

WORKDIR /workspace
COPY . .

#RUN apk add --no-cache --virtual .build-deps \
#        gcc libc-dev libffi-dev make openssl-dev tzdata musl-dev python-dev postgresql-dev \
#    && pip install -r requirements.txt \
#    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
#    && apk del .build-deps

CMD ./launch.sh
EXPOSE 80
