# Xinu Remote Servers

[![forthebadge](https://forthebadge.com/images/featured/featured-built-with-love.svg)](https://forthebadge.com)

Xinu's simple and elegant remote disk and file server.
*Note: the servers are mostly for simple demo and testing purposes. It is by far a secure implementation that you should roll out in the wild. Nonetheless it can serve it's purpose on LAN or small embedded devices. It is easy extendible :)

## Requirements
Any gcc and make will probably do!

## Building
`make`

## Running
./rfserver [port] or ./rdserver [port]

## tools/xinucli
A python client tool to interface with the remote file server. 

```
usage: xinucli.py [-h] [--port [PORT]] [--ip [IP]] {read,write,rm,stat,mkdir,rmdir} ...

UDP Client

options:
  -h, --help            show this help message and exit
  --port [PORT]         Port number (default: 53224)
  --ip [IP]             IP location (default: localhost)

subcommands:
  {read,write,rm,stat,mkdir,rmdir}
    read                Read from a file
    write               Write to a file
    rm                  Remove a file
    stat                Stat a file
    mkdir               Make a directory
    rmdir               Remove a directory
```
## Docker
Again: implementation is pretty raw. It is probably best to run it in a container. 
```
docker build -t xinu-remoteserver .
docker run --rm -p 53224:53224/udp --name little-xinu xinu-remoteserver:latest
```
Did not implement capture of keys, so kill by `docker container kill little-xinu`

## Tests
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/robinkrens/xinu-remoteservers/.github%2Fworkflows%2Fdocker_test.yml)

For more see: tools/xinucli/tests
