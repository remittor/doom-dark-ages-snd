
import sys

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

class SoundMetadata:
    def __init__(self):
        self.smdfn = 'soundmetadata.bin'
        self.fd = None

    def read_name(self, read_hash = 0):        
        name_hash = None
        if read_hash == 1:
            name_hash = int.from_bytes(self.fd.read(4), 'little')
        name_size = int.from_bytes(self.fd.read(4), 'little')
        if name_size == 0 or name_size > 100:
            pos = self.fd.tell()
            raise RuntimeError(f'Incorrect name_size = 0x{name_size:X} into 0x{pos:X}')
        name = self.fd.read(name_size)
        try:
            name = name.decode()
        except UnicodeDecodeError:
            pos = self.fd.tell() - name_size
            raise RuntimeError(f'Incorrect name {name} into 0x{pos:X}  k = {self.k}')
        if read_hash == 2:
            name_hash = int.from_bytes(self.fd.read(4), 'little')
        if name_hash is None:
            return name
        else:
            return name, name_hash

    def decode(self):
        self.fd = open(self.smdfn, 'rb')
        fcnt = int.from_bytes(self.fd.read(4), 'little')
        print(f'{fcnt=}')
        for num in range(0, fcnt):
            self.pos = self.fd.tell()
            fname, crc = self.read_name(2)
            vt = int.from_bytes(self.fd.read(1), 'little')
            dir_name = self.read_name()
            print(f'{crc:08X} [{vt}] {dir_name}/{fname}')
            if vt != 0 and vt != 1:
                pos = self.fd.tell()
                raise RuntimeError(f'Incorrect vt = {vt}  pos = 0x{pos:X}')

        pos = self.fd.tell()
        print(f'========= {pos:08} =================================================')
        
        fcnt = int.from_bytes(self.fd.read(4), 'little')
        print(f'====== {fcnt=}  =============')
        for num in range(0, fcnt):
            fname, crc = self.read_name(1)
            print(f'{crc:08X}: {fname}')
        
        fcnt = int.from_bytes(self.fd.read(4), 'little')
        print(f'====== {fcnt=}  ====================')
        for num in range(0, fcnt):
            fname, crc = self.read_name(2)
            print(f'{crc:08X}: {fname}')

        pos = self.fd.tell()
        print(f'========= {pos:08X} =================================================')

        for i in range(0, 2):
            bcnt = int.from_bytes(self.fd.read(4), 'little')
            print(f'======== {bcnt=} ============================================')
            for bn in range(0, bcnt):
                dirname, crc = self.read_name(1)
                fcnt = int.from_bytes(self.fd.read(4), 'little')
                print(f'====== {dirname=} {fcnt=} ====================')
                for num in range(0, fcnt):
                    fname, crc = self.read_name(1)
                    print(f'{crc:08X}:  {fname}')
         

        fcnt = int.from_bytes(self.fd.read(4), 'little')
        print(f'======== {fcnt=} ============================================')
        kk = 0
        for num in range(0, fcnt):
            self.pos = self.fd.tell()
            fname, crc = self.read_name(2)
            unk1 = self.fd.read(4)
            flags = self.fd.read(3)
            unk2 = self.fd.read(4)
            print(f'{crc:08X}: {unk1.hex()} {flags.hex()} {unk2.hex()} "{fname}"')
            flags = int.from_bytes(flags, 'little')
            if flags == 0:
                lang_cnt = int.from_bytes(self.fd.read(4), 'little')
                lang_list = [ ]
                for lang_num in range(0, lang_cnt):
                    lang_name, crc = self.read_name(2)
                    lang_list.append(lang_map[lang_name]) 
                print(f'  {"".join(lang_list)}')
                lang_cnt = int.from_bytes(self.fd.read(4), 'little')
                lang_list = [ ]
                for lang_num in range(0, lang_cnt):
                    lang_name, crc = self.read_name(1)
                    lang_list.append(lang_map[lang_name]) 
                print(f'  {"".join(lang_list)}')
            else:
                xcnt = int.from_bytes(self.fd.read(4), 'little')
                for i in range(0, xcnt):
                    dir_name, crc = self.read_name(1)
                    print(f'  {crc:08X}: {dir_name}')

        fcnt = int.from_bytes(self.fd.read(4), 'little')
        print(f'======== {fcnt=} ============================================')
        for num in range(0, fcnt):
            snd_name = self.read_name()
            num1 = int.from_bytes(self.fd.read(4), 'little')
            num2 = int.from_bytes(self.fd.read(4), 'little')
            inum = int.from_bytes(self.fd.read(4), 'little')
            print(f'0x{num1:02X} 0x{num2:02X} [items = {inum:04}] : {snd_name}')
            data = self.fd.read(inum * 4)

if __name__ == '__main__':
    smd = SoundMetadata()
    smd.decode()
