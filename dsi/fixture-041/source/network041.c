/* MIT — DSi RA Bridge 041: 030 wire transport + 033 external observer.
 * Only reads the tagged lab observer window. The default Calico/libnds ARM7
 * is used; NO custom ARM7, WiFi_TWL_Update() or retail game memory scan.
 *
 * In contrast with 030, the sample counter and buttons below come from
 * observer-041's IRQ-latched independent VBlank hook, not from this sender.
 */
#include <nds.h>
#include <calico.h>
#include <fat.h>
#include <dswifi9.h>
#include <wfc.h>
#include "wire.h"
#include "network041.h"
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/stat.h>

#define OBS_HEADER ((volatile uint8_t*)0x02200000u)
#define OBS_STATE  ((volatile uint32_t*)0x02202000u)
#define OBS_LATEST ((volatile uint32_t*)0x02202024u)
#define OBS_WINDOW_WATCH ((volatile uint32_t*)0x02200014u)
#define OBS_CAPACITY 1200u
#define NET_HZ 10u

enum {NET_OFF,NET_INIT,NET_ASSOC,NET_WAIT,NET_READY,NET_STOP,NET_NO_CONFIG,
      NET_NO_WIFI,NET_NO_PROFILE,NET_TIMEOUT,NET_SOCKET,NET_LOST,NET_NO_OBSERVER};
static const char *status_text[] = {"OFF","INIT","ASSOC","WAIT_PEER","READY",
  "STOPPED","NO_CFG","WIFI_FAIL","NO_PROFILE","TIMEOUT","SOCKET_FAIL",
  "LOST","NO_OBSERVER"};
static volatile int state=NET_OFF,stop_requested=0,done=1;
static volatile uint32_t sent=0;
static Thread worker;
static bool started=false;
static uint8_t worker_stack[32768] __attribute__((aligned(8)));
static uint8_t peer_ip[4];
static uint16_t peer_port=18216;
static uint32_t session,mode;

static bool elapsed(u64 t,u32 micros){return tickGetCount()-t>=ticksFromUsec(micros);}
static bool private_ipv4(unsigned a,unsigned b,unsigned c,unsigned d){
 (void)c;
 return a<=255&&b<=255&&c<=255&&d<=255&&d!=255&&
   (a==10||(a==172&&b>=16&&b<=31)||(a==192&&b==168));
}
static bool config_read(void){
 if(!fatInitDefault())return false;
 struct stat st;
 if(stat("sd:/",&st)||!S_ISDIR(st.st_mode))return false;
 FILE *f=fopen("sd:/DSiRABridge_041/receiver.cfg","r");
 if(!f)return false;
 char line[112];bool ok=false;
 if(fgets(line,sizeof(line),f)){
  unsigned a,b,c,d,p,hz;char trailing;
  int n=sscanf(line,"%u.%u.%u.%u %u %u %c",&a,&b,&c,&d,&p,&hz,&trailing);
  if(n==6&&private_ipv4(a,b,c,d)&&p>=1024&&p<=65535&&hz==NET_HZ){
   peer_ip[0]=a;peer_ip[1]=b;peer_ip[2]=c;peer_ip[3]=d;
   peer_port=(uint16_t)p;ok=true;
  }
 }
 fclose(f);
 return ok;
}
static bool observer_ready(void){
 if(memcmp((const void*)OBS_HEADER,"DSIOBS33",8))return false;
 /* Header 033 is 64 bytes, version 1, watched 20-byte fixture state. */
 const volatile uint32_t *h=(const volatile uint32_t*)0x02200008u;
 if(h[0]!=1||h[1]!=64||h[2]!=20||h[8]!=1200||h[7]!=32)return false;
 const volatile uint32_t *s=OBS_STATE;
 return !s[1]&&!s[7]&&!s[8]&&s[0]>0;
}
typedef struct {uint32_t counter,buttons,scanlines;} Latest;
/* The hook uses an even/odd sequence. Snapshot is never an unguarded
 * partial memcpy from a VBlank interrupt that can happen mid-copy. */
static bool observer_latest(Latest *out){
 if(!observer_ready())return false;
 uint32_t a=OBS_LATEST[0];
 if(a&1u||a==0)return false;
 __asm__ volatile ("" ::: "memory");
 uint32_t c=OBS_LATEST[1],buttons=OBS_LATEST[2],checksum=OBS_LATEST[3];
 uint32_t valid=OBS_LATEST[4],lines=OBS_LATEST[5];
 __asm__ volatile ("" ::: "memory");
 uint32_t b=OBS_LATEST[0];
 if(a!=b||b&1u||!valid||buttons>0x3ffu||checksum!=(c^buttons^0x9317A55Au))
  return false;
 out->counter=c;out->buttons=buttons;out->scanlines=lines;
 return true;
}
static bool valid_control(const uint8_t *b,unsigned n,uint32_t sess,uint32_t nonce){
 return n==20&&b[4]==1&&b[5]==1&&b[6]==mode&&b[7]==0&&
  get32(b+8)==sess&&get32(b+16)==crc32(b,16)&&
  (!memcmp(b,"DSA3",4)?get32(b+12)==nonce:!memcmp(b,"DSP3",4));
}
static int network_worker(void *unused){
 (void)unused;
 int fd=-1;bool wifi=false;
 if(!observer_ready()){state=NET_NO_OBSERVER;goto done;}
 if(!config_read()){state=NET_NO_CONFIG;goto done;}
 state=NET_INIT;
 if(!Wifi_InitDefault(INIT_ONLY)){state=NET_NO_WIFI;goto done;}
 wifi=true;
 if(stop_requested)goto stop;
 wfcLoadFromNvram();
 if(!wfcGetNumSlots()){state=NET_NO_PROFILE;goto done;}
 state=NET_ASSOC;
 if(!wfcBeginAutoConnect()){state=NET_NO_WIFI;goto done;}
 u64 since=tickGetCount();
 while(!stop_requested&&Wifi_AssocStatus()!=ASSOCSTATUS_ASSOCIATED){
  if(elapsed(since,30000000)){state=NET_TIMEOUT;goto done;}
  threadSleep(20000);
 }
 if(stop_requested)goto stop;
 fd=socket(AF_INET,SOCK_DGRAM,0);
 if(fd<0){state=NET_SOCKET;goto done;}
 int nonblock=1;
 if(ioctl(fd,FIONBIO,&nonblock)<0){state=NET_SOCKET;goto done;}
 struct sockaddr_in peer;memset(&peer,0,sizeof(peer));
 peer.sin_family=AF_INET;peer.sin_port=htons(peer_port);
 char addr[20];snprintf(addr,sizeof(addr),"%u.%u.%u.%u",
   peer_ip[0],peer_ip[1],peer_ip[2],peer_ip[3]);
 peer.sin_addr.s_addr=inet_addr(addr);
 mode=isDSiMode()?1:0;
 session=(uint32_t)tickGetCount()^0x41003341u;
 if(!session)session=1;
 uint32_t nonce=0xD531010Au,seq=0,last_counter=0;
 uint8_t packet[64],incoming[128];
 bool ready=false;u64 last_hello=0,last_data=0,waiting=tickGetCount();
 state=NET_WAIT;
 while(!stop_requested){
  if(Wifi_AssocStatus()!=ASSOCSTATUS_ASSOCIATED){state=NET_LOST;goto done;}
  if(!last_hello||elapsed(last_hello,1000000)){
   wire_control(packet,"DSH3",1,mode,session,nonce);
   sendto(fd,packet,20,0,(struct sockaddr*)&peer,sizeof(peer));
   last_hello=tickGetCount();
  }
  for(unsigned i=0;i<8;i++){
   struct sockaddr_in from;socklen_t nfrom=sizeof(from);
   int n=recvfrom(fd,incoming,sizeof(incoming),0,(struct sockaddr*)&from,&nfrom);
   if(n<0)break;
   if(from.sin_port!=peer.sin_port||from.sin_addr.s_addr!=peer.sin_addr.s_addr||
      !valid_control(incoming,(unsigned)n,session,nonce))continue;
   if(!memcmp(incoming,"DSA3",4)){ready=true;state=NET_READY;}
   else if(!memcmp(incoming,"DSP3",4)){
    uint32_t ping=get32(incoming+12);
    wire_control(packet,"DSO3",1,mode,session,ping);
    sendto(fd,packet,20,0,(struct sockaddr*)&peer,sizeof(peer));
   }
  }
  if(!ready&&elapsed(waiting,12000000)){state=NET_TIMEOUT;goto done;}
  if(ready&&(!last_data||elapsed(last_data,100000))){ /* max ~10 UDP samples per second */
   Latest snap;
   if(observer_latest(&snap)&&snap.counter>last_counter){
    uint32_t words[4]={0x44534931u,snap.counter,snap.buttons,
                        snap.counter^snap.buttons^0xA5A55A5Au};
    uint32_t watched=*OBS_WINDOW_WATCH;
    /* Emit only the fixture's whitelisted low ARM9 watch address. */
    if(watched>=0x02000000u&&watched<=0x02100000u-20u&&!(watched&3u)){
     wire_sample(packet,1,mode,session,seq,snap.counter,snap.scanlines,0,watched,words);
     if(sendto(fd,packet,64,0,(struct sockaddr*)&peer,sizeof(peer))==64){
      last_counter=snap.counter;seq++;sent++;
     }
    }
   }
   last_data=tickGetCount();
  }
  threadSleep(2000);
 }
stop:
 state=NET_STOP;
done:
 if(fd>=0)closesocket(fd);
 if(wifi)Wifi_DisconnectAP();
 done=1;
 return 0;
}
void network041_start(void){
 if(started||!done)return;
 stop_requested=0;sent=0;done=0;state=NET_INIT;
 threadPrepare(&worker,network_worker,NULL,worker_stack+sizeof(worker_stack),MAIN_THREAD_PRIO+1);
 threadAttachLocalStorage(&worker,NULL);
 started=true;threadStart(&worker);
}
void network041_stop(void){stop_requested=1;}
void network041_poll(void){
 if(started&&done){threadJoin(&worker);started=false;}
}
bool network041_done(void){return done&&!started;}
const char *network041_status(void){
 unsigned id=(unsigned)state;return id<sizeof(status_text)/sizeof(status_text[0])?status_text[id]:"UNKNOWN";
}
uint32_t network041_sent(void){return sent;}
