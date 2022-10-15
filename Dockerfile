FROM ubuntu:focal

EXPOSE 80

RUN apt update
RUN apt install -y curl xz-utils less python3

RUN ln -sf /videos /root/videos
COPY video-server.py /root/
COPY index.html /root/
CMD cd /root/ && python3 video-server.py 0.0.0.0 80 videos

