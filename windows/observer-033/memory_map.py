"""MIT. Pure host mapping of validated snapshots, never physical dereferencing.
RA DS offsets follow official consoleinfo.c, not a blanket native-address addition."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Snapshot:
    main: bytes
    dtcm: bytes
    dtcm_base: int
    dsi: bool=False
    def __post_init__(self):
        if len(self.main)!=(0x1000000 if self.dsi else 0x400000) or len(self.dtcm)!=0x4000:raise ValueError("complete region lengths")
        if not 0<=self.dtcm_base<=0xffffc000 or self.dtcm_base&0xfff:raise ValueError("actual CP15 DTCM base")
    def read(self,offset,size):
        if not isinstance(offset,int) or not isinstance(size,int) or size<1 or size>4 or offset<0:raise ValueError("read request")
        if offset<=len(self.main)-size:return self.main[offset:offset+size]
        if 0x1000000<=offset<=0x1004000-size:
            p=offset-0x1000000;return self.dtcm[p:p+size]
        return None # short read must disable/suspend evaluation, not invent memory
    def native_to_ra(self,address,size=1):
        if not 1<=size<=4 or not 0<=address<=0xffffffff:raise ValueError("native request")
        if self.dtcm_base<=address<=self.dtcm_base+0x4000-size:return 0x1000000+address-self.dtcm_base
        if 0x02000000<=address<=0x02000000+len(self.main)-size:return address-0x02000000
        return None
