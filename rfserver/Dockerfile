# Use Alpine Linux as base image
FROM alpine

# update and install cross compiler
RUN apk update && \
    apk add --no-cache gcc-arm-none-eabi 

# required build tools
RUN apk add flex flex-dev bison gawk make libc-dev

# Set working directory
WORKDIR /home

# Copy current files into /home
COPY . .

# Run make in /home
RUN make clean && make

# Copy rfsserver to /srv
RUN cp rfserver /srv/

# Expose port 12345/udp
EXPOSE 53224/udp

# Define the entry point for your container
ENTRYPOINT ["/srv/rfserver"]
