import struct

"""
Message struct is this 
{
unsigned int sig,       for len 0:4
unsigned int totlen,    for len 4:8
unsigned int type,      for len 8:12
char[]       data       for len 12:totlen
}
"""

message_sig = 0xA187A278
message_echo_type = 0x1234

parse_error = 0
buffer_not_enough = 1
parse_ok = 2

def remove_message(buf):
    if len(buf) < 12:
        return buffer_not_enough, None, buf

    buf = ''.join(buf)

    if not struct.unpack('!I', buf[:4])[0] == message_sig:
        #print struct.unpack('!I', buf[:4])[0]
        return parse_error, None, list(buf)

    totlen, type = struct.unpack('!II', buf[4:12])
    #type = struct.unpack('!I', buf[8:12])[0]

    if totlen <= len(buf):
        data = buf[12:totlen]
        buf = buf[totlen:]
        return parse_ok, (type, data), list(buf)
    else:
        return buffer_not_enough, None, list(buf)

def extend_message(buf, type, data):
    message = struct.pack('!3I' + str(len(data)) + 's', message_sig, len(data) + 12, type, data)
    buf.extend(message)
    return buf


if __name__ == '__main__':
    buf = extend_message([], message_echo_type, "123131949179374aaiuevavainveoivnaonevaeivaoveivaoeiioaf10112094fhweh")
    print len(buf)

