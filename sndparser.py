
import os
import sys
import io
import optparse

parser = optparse.OptionParser("usage: %prog [options]")
parser.add_option("-f", "--file", dest="file", default = None)
parser.add_option("-c", "--conf", dest="confgen", action="store_true", default = False)
parser.add_option("-q", "--qrcode", dest="qrcode", action="store_true", default = False)
parser.add_option("-a", "--add", dest="addcl", default = "")
parser.add_option("-u", "--update", dest="update", default = "")
parser.add_option("-d", "--delete", dest="delete", default = "")
parser.add_option("-i", "--ipaddr", dest="ipaddr", default = "")
parser.add_option("-p", "--port", dest="port", default = None, type = 'int')
parser.add_option("", "--make", dest="makecfg", default = "")
parser.add_option("", "--tun", dest="tun", default = "")
parser.add_option("", "--create", dest="create", action="store_true", default = False)
(opt, args) = parser.parse_args()

lang_map = {
   'English(US)': 'E',
   'French(France)': 'F',
   'German': 'G',
   'Italian': 'I',
   'Japanese': 'J',
   'Polish': 'P',
   'Portuguese(Brazil)': 'B',
   'Russian': 'R',
   'Spanish(Mexico)': 'M',
   'Spanish(Spain)': 'S',
}

class DataReader(io.BytesIO):
    def __init__(self, stream, addr = 0):
        self.addr = addr
        self.is_file = False        
        self.s_size = None
        if isinstance(stream, str):
            self.s_size = os.path.getsize(stream)
            self.stream = open(stream, 'rb')
            self.is_file = True
        elif isinstance(stream, bytes):
            self.s_size = len(stream)
            self.stream = io.BytesIO(stream)
        elif isinstance(stream, io.BytesIO):
            stream = stream.getvalue()
            self.s_size = len(stream)
            self.stream = io.BytesIO(stream)
        else:
            raise ValueError(f'Incorrect type of stream argument')
        self.stream.seek(0)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.stream)

    next = __next__

    def readable(self):
        return True

    def seekable(self):
        return True

    def writable(self):
        return False

    def readline(self):
        raise RuntimeError('Method readline not supported')

    def readlines(self):
        raise RuntimeError('Method readlines not supported')

    def write(self, data):
        raise IOError('Stream is not writeable')

    @property
    def eof(self):
        return self.cur_pos >= self.s_size

    @property
    def cur_pos(self):
        return self.stream.tell()

    def tell(self):
        return self.stream.tell()
        
    def seek(self, offset, whence = os.SEEK_SET):
        self.stream.seek(offset, whence)

    def getbuffer(self):
        if self.is_file:
            pos = self.cur_pos
            self.stream.seek(0)
            data = self.stream.read()
            self.stream.seek(pos)
            return data
        else:
            return self.stream.getbuffer()

    def read(self, size, check = True):
        if not isinstance(size, int) or size <= 0:
            raise ValueError(f'Incorrect size = {size}')
        data = self.stream.read(size)
        if check:
            if len(data) < size:
                pos = self.addr + self.cur_pos
                raise EOFError(f'EOF at pos = 0x{pos:X}')
        return data

    def read_uint(self, size = 4):
        data = self.read(size)
        return int.from_bytes(data, 'little')

    def read_str(self, size, strip = True, check = True):
        if not isinstance(size, int) or size <= 0:
            raise ValueError(f'Incorrect size = {size}')
        pos = self.addr + self.cur_pos
        string = self.read(size, check = check)
        try:
            string = string.decode()
        except UnicodeDecodeError:
            raise RuntimeError(f'Incorrect string {string} into 0x{pos:X}')
        if strip:
            string = string.strip()
        return string

    def read_name(self, max_len = 127):
        name_size = self.read_uint()
        pos = self.addr + self.cur_pos
        if name_size == 0 or name_size > max_len:
            raise RuntimeError(f'Incorrect name_size = 0x{name_size:X} into 0x{pos:X}')
        name = self.read(name_size)
        try:
            name = name.decode()
        except UnicodeDecodeError:
            raise RuntimeError(f'Incorrect name {name} into 0x{pos:X}')
        return name

class SoundMetadata:
    def __init__(self):
        self.smdfn = 'soundmetadata.bin'
        self.stream = DataReader(self.smdfn)

    def decode(self):
        stream = self.stream
        fcnt = stream.read_uint()
        print(f'{fcnt=}')
        for num in range(0, fcnt):
            fname = stream.read_name()
            val = stream.read_uint()
            vt = stream.read_uint(1)
            if vt != 0 and vt != 1:
                raise RuntimeError(f'Incorrect vt = {vt}  pos = 0x{stream.cur_pos:X}')
            dir_name = stream.read_name()
            print(f'{val:08X} [{vt}] {dir_name}/{fname}')

        #print(f'========= {stream.cur_pos:08X} =================================================')
        
        fcnt = stream.read_uint()
        print(f'====== {fcnt=}  =============')
        for num in range(0, fcnt):
            val = stream.read_uint()
            fname = stream.read_name()
            print(f'{val:08X}: {fname}')
        
        fcnt = stream.read_uint()
        print(f'====== {fcnt=}  ====================')
        for num in range(0, fcnt):
            fname = stream.read_name()
            val = stream.read_uint()
            print(f'{val:08X}: {fname}')

        #print(f'========= {stream.cur_pos:08X} =================================================')

        for i in range(0, 2):
            bcnt = stream.read_uint()
            print(f'======== {bcnt=} ============================================')
            for bn in range(0, bcnt):
                val = stream.read_uint()
                dirname = stream.read_name()
                fcnt = stream.read_uint()
                print(f'====== {val:08X}: "{dirname}" ({fcnt=}) ====================')
                for num in range(0, fcnt):
                    val = stream.read_uint()
                    fname = stream.read_name()
                    print(f'{val:08X}:  {fname}')

        fcnt = stream.read_uint()
        print(f'======== {fcnt=} ============================================')
        kk = 0
        for num in range(0, fcnt):
            fname = stream.read_name()
            val = stream.read_uint()
            unk1 = stream.read_uint()
            f0 = stream.read_uint(1)
            f1 = stream.read_uint(1)
            f2 = stream.read_uint(1)
            unk2 = stream.read_uint()
            print(f'{val:08X}: {unk1:08X} {f0}-{f1}-{f2} {unk2:08X} "{fname}"  [{num}/{fcnt}]')
            if f1 == 0:
                lang_cnt = stream.read_uint()
                lang_list = [ ]
                for lang_num in range(0, lang_cnt):
                    lang_name = stream.read_name()
                    val = stream.read_uint()
                    print(f'  {val:08X}: {lang_name}')
                    lang_list.append(lang_map[lang_name])
                print(f'  {"".join(lang_list)}')
                lang_cnt = stream.read_uint()
                lang_list = [ ]
                for lang_num in range(0, lang_cnt):
                    val = stream.read_uint()
                    lang_name = stream.read_name()
                    print(f'  {val:08X}: {lang_name}')
                    lang_list.append(lang_map[lang_name]) 
                print(f'  {"".join(lang_list)}')
            else:
                xcnt = stream.read_uint()
                for i in range(0, xcnt):
                    val = stream.read_uint()
                    dir_name = stream.read_name()
                    print(f'  {val:08X}: {dir_name}')

        fcnt = stream.read_uint()
        print(f'======== {fcnt=} ============================================')
        for num in range(0, fcnt):
            snd_name = stream.read_name()
            num1 = stream.read_uint()
            num2 = stream.read_uint()
            inum = stream.read_uint()
            print(f'0x{num1:02X} 0x{num2:02X} [items = {inum:04}] : {snd_name}')
            data = stream.read(inum * 4)

class WaveSound:
    def __init__(self, filename):
        self.filename = filename
        self.stream = DataReader(self.filename)

    @property
    def cur_pos(self):
        return self.stream.cur_pos
    
    def decode(self):
        stream = self.stream
        ver = stream.read_uint()
        print(f'File "{self.filename}"  {ver=}')
        xsize = stream.read_uint()
        print(f'{xsize=:08X}')
        blk_end = stream.cur_pos - 4 + xsize
        #blk_size = stream.read_uint()
        #blk_end = stream.cur_pos - 4 + blk_size

        hdr_size = stream.read_uint()
        hdr_end = stream.cur_pos - 4 + hdr_size
        #print(f'{blk_size=:08X}  {hdr_size=:08X}')

        for withdata in range(0, 2):
            print(f'{hdr_size=:08X}  {hdr_end=:08X}  {withdata=}')
            rk = 0
            while True:
                rk += 1
                pos = stream.addr + stream.cur_pos
                if not withdata and pos >= hdr_end:
                    break                    
                if stream.eof:
                    print(f'END of File "{self.filename}" (pos = 0x{pos:08X}) {withdata=}')
                    return
                magic = stream.read(4)
                if magic != b'RIFF':
                    raise RuntimeError(f'Expected "RIFF", but readed {magic}  (pos = 0x{pos:X})')
                rsize = stream.read_uint()
                if rsize < 24:
                    raise RuntimeError(f'Expected RIFF size = {rsize}  (pos = 0x{pos:X})')
                stream.seek(-8, os.SEEK_CUR)
                riff = stream.read(8 + rsize, check = True if withdata else False)
                riff = DataReader(riff, pos)
                if withdata and rk < 8:
                    fn = os.path.basename(self.filename) + f'__{rk}.wav'
                    with open(fn, 'wb') as file:
                        file.write(riff.getbuffer())
                magic = riff.read(4)
                rsize = riff.read_uint()
                wave = riff.read(4)
                if wave != b'WAVE':
                    raise RuntimeError(f'Expected "WAVE", but readed {wave}  (pos = 0x{pos:X})')
                print(f'{pos:08X}: RIFF-WAVE with size = 0x{rsize:X} <{withdata}>')
                while True:
                    name = riff.read(4)
                    name = name.decode().rstrip()
                    size = riff.read_uint()
                    if name not in [ 'fmt', 'hash', 'smpl', 'akd', 'cue', 'LIST', 'seek', 'junk', 'data' ]:
                        raise RuntimeError(f'Incorrect area name = {name} (pos = {pos:08X})')
                    print(f'  {name:4s}: size = 0x{size:X}')
                    if name == 'LIST':
                        data = riff.read(size)
                        self.decode_LIST(data, stream.addr + stream.cur_pos - size)
                        continue
                    if name == 'data':
                        if withdata:
                            data = riff.read(size)
                        else:
                            stream.seek(pos - stream.addr + riff.cur_pos)
                        break
                    data = riff.read(size)
                    pass
                pass
            pass
            #data_size = blk_end - self.cur_pos
            aux_size = xsize - hdr_size
            aux = stream.read(aux_size)
            #fn = os.path.basename(self.filename) + '__aux.dat'
            #with open(fn, 'wb') as file:
            #    file.write(aux)
            aux = DataReader(aux)
            aux_num = aux.read_uint()
            print(f'===== {aux_num=} ============================================')
            for anum in range(0, aux_num):
                data = aux.read(28)
                offset = aux.read_uint() + 0x0C
                print(f'{offset:08X}: {data.hex()}')
            print('========================================================')
            print(f'blk end = {stream.cur_pos:X}')
            
    def decode_LIST(self, data, addr):
        stream = DataReader(data, addr = addr)
        stream.seek(8) # skip "adtllabl" prefix
        while True:
            msize = stream.read_uint()
            mtype = stream.read_uint()
            mname = stream.read_str(msize - 4)
            mname = mname.replace('\0', '')
            print(f'    MARKER: "{mname}" (type = 0x{mtype:X})')
            break # FIXME
        sz = stream.s_size - stream.cur_pos
        if sz > 0:
            print(f'    RAWDATA: {data}')

if __name__ == '__main__':
    if opt.file:
        snd = WaveSound(opt.file)
        snd.decode()
    else:
        smd = SoundMetadata()
        smd.decode()
