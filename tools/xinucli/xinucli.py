import sys
import argparse
import socket
import struct
import logging
import configparser

# file modes
FMODE = {
    'F_MODE_R': 0x01,
    'F_MODE_W': 0x02,
    'F_MODE_RW': 0x03,
    'F_MODE_N': 0x04,
    'F_MODE_O': 0x08,
    'F_MODE_NO': 0x04 | 0x08  # F_MODE_N | F_MODE_O
}

# file and directory control
CTLS = {
    'F_CTL_DEL': 1,         # Delete a file
    'F_CTL_TRUNC': 2,       # Truncate a file
    'F_CTL_MKDIR': 3,       # Make a directory
    'F_CTL_RMDIR': 4,       # Remove a directory
    'F_CTL_SIZE': 5,        # Obtain the size of a file
    'F_CTL_LS': 6           # List files in a directory
}
    
RF_MSG_RREQ = 0x0001    # Read Request
RF_MSG_WREQ = 0x0002    # Write Request
RF_MSG_OREQ = 0x0003    # Open request
RF_MSG_DREQ = 0x0004    # Delete request
RF_MSG_TREQ = 0x0005    # Truncate request
RF_MSG_SREQ = 0x0006    # Size request    
RF_MSG_MREQ = 0x0007    # Mkdir request 
RF_MSG_XREQ = 0x0008    # Rmdir request
RF_MSG_CREQ = 0x0009    # Close request    
RF_MSG_RESPONSE = 0x0100      # Bit indicating response

RF_MSGLEN = 1024
RF_NAMLEN = 128
RF_HDRLEN = RF_NAMLEN + 8
RF_TOTAL = RF_HDRLEN + RF_MSGLEN + 8

class FileClient:

    def __init__(self, ip='localhost', port=53224):
        self.ip = ip
        self.port = port
        self.seq = 0

    def _send_receive(self, req):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(req, (self.ip, self.port))
                packed_data, addr = s.recvfrom(RF_TOTAL)
                return packed_data
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def _pack_message(self, message_format, *args):
        return struct.pack(message_format, *args)

    def unpack_hdr(self, packed):
        assert len(packed) == RF_HDRLEN
    
        message_format = "!HHI128s"
        rf_type, rf_status, rf_seq, rf_name = struct.unpack(message_format, packed)
        
        if (rf_seq != self.seq):
            raise Exception('sequence incorrect!')
    
        if (rf_status != 0x0):
            raise Exception('err: file operation failed!')

        return rf_type, rf_name

    def open_f(self, filename, mode=0x03):  # Default mode: RF_MODE_RW
        assert len(filename) < RF_NAMLEN
        message_format = "!HHI128sI"
        self.seq += 1
        return self._pack_message(message_format, RF_MSG_OREQ, 0, self.seq, filename.encode('utf-8'), mode)

    def close_f(self, filename):
        assert len(filename) < RF_NAMLEN
        message_format = "!HHI128s"
        self.seq += 1
        return self._pack_message(message_format, RF_MSG_CREQ, 0, self.seq, filename.encode('utf-8'))

    def read_f(self, filename, pos=0, size=1024):
        assert len(filename) < RF_NAMLEN
        message_format = "!HHI128sII"
        self.seq += 1
        return self._pack_message(message_format, RF_MSG_RREQ, 0, self.seq, filename.encode('utf-8'), pos, size)

    def write_f(self, filename, data, pos=0):
        assert len(filename) < RF_NAMLEN
        message_format = f'!HHI128sII{len(data)}s'
        self.seq += 1
        return self._pack_message(message_format, RF_MSG_WREQ, 0, self.seq, filename.encode('utf-8'), pos, len(data), data.encode('utf-8'))

    def del_f(self, filename, truncate=False):
        assert len(filename) < RF_NAMLEN
        message_format = "!HHI128s"
        self.seq += 1
        rf_type = RF_MSG_TREQ if truncate else RF_MSG_DREQ
        return self._pack_message(message_format, rf_type, 0, self.seq, filename.encode('utf-8'))

    def stat_f(self, filename):
        assert len(filename) < RF_NAMLEN
        message_format = "!HHI128s"
        self.seq += 1
        return self._pack_message(message_format, RF_MSG_SREQ, 0, self.seq, filename.encode('utf-8'))
    
    def mkdir_f(self, dirname):
        assert len(dirname) < RF_NAMLEN
        message_format = "!HHI128s"
        self.seq += 1
        return self._pack_message(message_format, RF_MSG_MREQ, 0, self.seq, dirname.encode('utf-8'))
    
    def rmdir_f(self, dirname):
        assert len(dirname) < RF_NAMLEN
        message_format = "!HHI128s"
        self.seq += 1
        return self._pack_message(message_format, RF_MSG_XREQ, 0, self.seq, dirname.encode('utf-8'))

    def exec_req(self, req):
        packed_data = self._send_receive(req)
        if packed_data:
            t, n = self.unpack_hdr(packed_data[:RF_HDRLEN])

            if t & RF_MSG_SREQ == RF_MSG_SREQ: # no single bits used for flags(!)
                rf_size = struct.unpack('!I', packed_data[RF_HDRLEN:RF_HDRLEN+4])
                print("size:", rf_size[0])
            elif t & RF_MSG_OREQ == RF_MSG_OREQ:
                rf_mode = struct.unpack('!I', packed_data[RF_HDRLEN:RF_HDRLEN+4])
                logging.info(f'mode: {rf_mode[0]}')
            elif t & RF_MSG_CREQ == RF_MSG_CREQ:
                logging.info('file closed')
            elif t & RF_MSG_TREQ == RF_MSG_TREQ:
                logging.info('file truncated')
            elif t & RF_MSG_DREQ == RF_MSG_DREQ:
                logging.info('file deleted')
            elif (t & RF_MSG_RREQ == RF_MSG_RREQ or t & RF_MSG_WREQ == RF_MSG_WREQ ):
                rf_pos, rf_len = struct.unpack('!II',packed_data[RF_HDRLEN:RF_HDRLEN+8])
                logging.info(f'read/wrote {rf_len} bytes')
                if (t & RF_MSG_RREQ): # only for reads: read data response
                    format_message = f'!{rf_len}s'
                    (rf_data) = struct.unpack(format_message, packed_data[RF_HDRLEN+8:RF_HDRLEN+8+rf_len])
                    print(rf_data[0].decode())

    def main(self):
        parser = argparse.ArgumentParser(description="UDP Client")
        parser.add_argument("--port", type=int, nargs="?", default=53224, help="Port number (default: 53224)")
        parser.add_argument("--ip", nargs="?", default="localhost", help="IP location (default: localhost)")

        subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

        # Subparsers definition
        read_parser = subparsers.add_parser("read", help="Read from a file")
        read_parser.add_argument("filename", type=str, help="Name of the file to read from")
        read_parser.add_argument("--length", type=int, default=1024, help="Number of bytes to read (default: 1024)")
        read_parser.add_argument("--fileposition", type=int, default=0, help="Starting position in the file (default: 0)")

        write_parser = subparsers.add_parser("write", help="Write to a file")
        write_parser.add_argument("filename", type=str, help="Name of the file to write to")
        write_parser.add_argument("data", type=str, help="Data to write to the file")
        write_parser.add_argument("--fileposition", type=int, default=0, help="Starting position in the file (default: 0)")

        rm_parser = subparsers.add_parser("rm", help="Remove a file")
        rm_parser.add_argument("filename", help="Name of the file to remove")
        rm_parser.add_argument("--truncate", action="store_const", const=True, default=False, help="Do not delete: truncate")
        
        stat_parser = subparsers.add_parser("stat", help="Stat a file")
        stat_parser.add_argument("filename", help="Name of the file to stat")

        mkdir_parser = subparsers.add_parser("mkdir", help="Make a directory")
        mkdir_parser.add_argument("dir", help="Name of the directory to create")

        rmdir_parser = subparsers.add_parser("rmdir", help="Remove a directory")
        rmdir_parser.add_argument("dir", help="Name of the directory to remove")

        args = parser.parse_args()

        self.port = args.port
        self.ip = args.ip

        logging.basicConfig(stream=sys.stderr, level=logging.INFO)

        config = configparser.ConfigParser()
        config.read('config.ini')
        self.seq = int(config.get('Settings', 'sequence'))

        if args.subcommand == "read":
            req = self.open_f(args.filename)
            self.exec_req(req)
            req = self.read_f(args.filename, pos=args.fileposition, size=args.length)
            self.exec_req(req)
            req = self.close_f(args.filename)
            self.exec_req(req)
        elif args.subcommand == "write":
            req = self.open_f(args.filename)
            self.exec_req(req)
            req = self.write_f(args.filename, args.data, pos=args.fileposition)
            self.exec_req(req)
            req = self.close_f(args.filename)
            self.exec_req(req)
        elif args.subcommand == "stat":
            req = self.stat_f(args.filename)
            self.exec_req(req)
        elif args.subcommand == "rm":
            req = self.del_f(args.filename, truncate=args.truncate)
            self.exec_req(req)
        elif args.subcommand == "mkdir":
            req = self.mkdir_f(args.dir)
            self.exec_req(req)
        elif args.subcommand == "rmdir":
            req = self.rmdir_f(args.dir)
            self.exec_req(req)
        else:
            print("No subcommand provided")

        config.set('Settings', 'sequence', str(self.seq))
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

if __name__ == "__main__":
    client = FileClient()
    client.main()

