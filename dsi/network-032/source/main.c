/* DSi RA Bridge 0.3.2. MIT. Standalone controlled-memory network probe.
 * No NAND writes, no credentials/config writes, no game hooks.
 * Modern libnds/Calico + dswifi; default ARM7 driver, no custom firmware.
 */
#include <nds.h>
#include <calico.h>
#include <fat.h>
#include <dswifi9.h>
#include <wfc.h>
#include "wire.h"
#include "reliable.h"
#include <time.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>
#define RECORDS 600
enum { IDLE, INITIALIZING, ASSOCIATING, WAIT_RECEIVER, READY, INIT_FAILED, LINK_TIMEOUT, PEER_TIMEOUT, SOCKET_FAILED, STOPPED, LINK_LOST, NO_PROFILES, DRAINING, COMPLETE, RETRY_FAILED, DRAIN_FAILED };
static const char *stages[]={"IDLE","INIT","ASSOC/DHCP","WAIT RECEIVER","READY","INIT FAILED","LINK TIMEOUT","PEER TIMEOUT","SOCKET FAILED","STOPPED","LINK LOST","NO SAVED PROFILES","DRAINING","COMPLETE","RETRY FAILED","DRAIN FAILED"};
static volatile int stage=IDLE,stop_requested=0,worker_done=1;
static Thread worker;
static bool worker_started=false;
static uint8_t worker_stack[32768] __attribute__((aligned(8)));
static uint8_t capture[RECORDS][64],tx_outcome[RECORDS];
static RSender tx;
static volatile int drain_requested=0;
static uint32_t session_hi=1;
static uint32_t hello_attempts=0,pong_attempts=0,ack_received=0,ping_received=0,ignored_controls=0;
static uint32_t sample_phase=0;
static volatile uint32_t session=1,send_errors=0,sent=0,overflows=0,peer_replies=0;
static volatile unsigned saved_profiles=0;
static uint32_t frame=0,sequence=0,captured=0,last_read_ticks=0;
static uint8_t ip[4]={192,168,0,2};
static unsigned port=18216,rate=10,field=0;
static bool offline=false,streaming=false,twl=false,fs_ready=false,exiting=false;
static u64 started_at=0,exit_at=0;
static char local_ip[24]="not connected",message[72]="Y connect; no permanent changes";
static volatile uint32_t controlled[4] __attribute__((aligned(16)));
static bool private_ip(void){return ip[3]!=255&&(ip[0]==10||(ip[0]==172&&ip[1]>=16&&ip[1]<=31)||(ip[0]==192&&ip[1]==168));}
static bool elapsed(u64 since,u32 usec){return tickGetCount()-since>=ticksFromUsec(usec);}
static uint32_t now_ms(void){return (uint32_t)((tickGetCount()*1000)/TICK_FREQ);}
static void send_status(int fd,const struct sockaddr_in*peer,uint32_t state){
 uint8_t packet[96],data[64];IrqState irq=irqLock();
 uint32_t v[16]={captured,tx.queued,tx.original_attempts,tx.original_accepted,tx.send_failed,
  tx.retry_attempts,tx.retry_accepted,tx.acked,r_pending(&tx),tx.peak,tx.backpressure,
  tx.exhausted,tx.ack_rx,tx.ack_duplicate,tx.rto,tx.capture_ack_max};
 for(unsigned i=0;i<16;i++)put32(data+i*4,v[i]);
 r_wire(packet,R_STATUS,1,twl?1:0,session,session_hi,tx.next,state,RECORDS,false,data);irqUnlock(irq);
 if(sendto(fd,packet,96,0,(const struct sockaddr*)peer,sizeof(*peer))!=96)send_errors++;
}
static int network_worker(void*arg){
 (void)arg;int fd=-1;bool initialized=false;
 stage=INITIALIZING;
 if(!Wifi_InitDefault(INIT_ONLY)){stage=INIT_FAILED;goto done;}
 initialized=true;if(stop_requested)goto stopped;
 wfcLoadFromNvram();saved_profiles=wfcGetNumSlots();
 if(!saved_profiles){stage=NO_PROFILES;goto done;}
 stage=ASSOCIATING;
 if(!wfcBeginAutoConnect()){stage=LINK_TIMEOUT;goto done;}
 u64 association=tickGetCount();
 while(!stop_requested&&Wifi_AssocStatus()!=ASSOCSTATUS_ASSOCIATED){
  if(elapsed(association,30000000)){stage=LINK_TIMEOUT;goto done;}
  threadSleep(20000);
 }
 if(stop_requested)goto stopped;
 struct in_addr addr;addr.s_addr=Wifi_GetIP();
 const char*addr_text=inet_ntoa(addr);
 IrqState irq=irqLock();snprintf(local_ip,sizeof(local_ip),"%s",addr_text);irqUnlock(irq);
 fd=socket(AF_INET,SOCK_DGRAM,0);
 if(fd<0){stage=SOCKET_FAILED;goto done;}
 int nonblock=1;
 if(ioctl(fd,FIONBIO,&nonblock)<0){stage=SOCKET_FAILED;goto done;}
 struct sockaddr_in peer;memset(&peer,0,sizeof(peer));peer.sin_family=AF_INET;peer.sin_port=htons(port);
 char peer_ip[24];snprintf(peer_ip,sizeof(peer_ip),"%u.%u.%u.%u",ip[0],ip[1],ip[2],ip[3]);
 peer.sin_addr.s_addr=inet_addr(peer_ip);
 uint8_t packet[96],incoming[128];RPacket reply;
 u64 last_hello=0,waiting=tickGetCount(),last_peer=tickGetCount(),last_status=0,drain_at=0,last_fin=0;
 unsigned fin_attempts=0;u64 progress_at=tickGetCount();uint32_t progress_base=0;stage=WAIT_RECEIVER;
 while(!stop_requested){
  uint32_t now=now_ms();
  if(Wifi_AssocStatus()!=ASSOCSTATUS_ASSOCIATED){stage=LINK_LOST;goto done;}
  if(!last_hello||elapsed(last_hello,1000000)){
   r_wire(packet,R_HELLO,1,twl?1:0,session,session_hi,0,rate,RECORDS,false,NULL);hello_attempts++;
   if(sendto(fd,packet,96,0,(struct sockaddr*)&peer,sizeof(peer))!=96)send_errors++;
   last_hello=tickGetCount();
  }
  for(int i=0;i<16;i++){
   struct sockaddr_in from;socklen_t from_len=sizeof(from);
   int n=recvfrom(fd,incoming,sizeof(incoming),0,(struct sockaddr*)&from,&from_len);
   if(n<0)break;
   if(from.sin_addr.s_addr!=peer.sin_addr.s_addr||from.sin_port!=peer.sin_port||
     !r_parse(&reply,incoming,(unsigned)n)||reply.lo!=session||reply.hi!=session_hi||
     reply.source!=1||reply.mode!=(twl?1:0)){ignored_controls++;continue;}
   if(reply.kind==R_ACK){
    irq=irqLock();bool accepted=r_ack(&tx,reply.seq,reply.a,reply.b,now);irqUnlock(irq);
    if(accepted){last_peer=tickGetCount();stage=drain_requested?DRAINING:READY;peer_replies++;ack_received++;}
   }else if(reply.kind==R_PING){
    r_wire(packet,R_PONG,1,twl?1:0,session,session_hi,reply.seq,0,0,false,NULL);
    pong_attempts++;ping_received++;
    if(sendto(fd,packet,96,0,(struct sockaddr*)&peer,sizeof(peer))!=96)send_errors++;
   }else if(reply.kind==R_FINACK&&drain_requested&&reply.seq==tx.next&&!r_pending(&tx)){
    stage=COMPLETE;goto done;
   }else ignored_controls++;
  }
  if(stage==WAIT_RECEIVER&&elapsed(waiting,10000000)){stage=PEER_TIMEOUT;goto done;}
  if((stage==READY||stage==DRAINING)&&elapsed(last_peer,5000000)){
   stage=WAIT_RECEIVER;waiting=tickGetCount(); /* retain every unacknowledged snapshot */
  }
  if(stage==READY||stage==DRAINING){
   for(unsigned budget=0;budget<4;budget++){
    irq=irqLock();REntry*entry=r_due(&tx,now);irqUnlock(irq);if(!entry)break;
    uint32_t seq=entry->seq;unsigned attempt=entry->attempts+1;
    r_wire(packet,R_DATA,1,twl?1:0,session,session_hi,seq,attempt,entry->capture_ms,attempt>1,entry->data);
    bool success=sendto(fd,packet,96,0,(struct sockaddr*)&peer,sizeof(peer))==96;
    irq=irqLock();r_sent(&tx,entry,now,success);if(seq<RECORDS)tx_outcome[seq]=entry->attempts;irqUnlock(irq);
    if(success)sent++;else send_errors++;
   }
  }
  if(drain_requested&&!drain_at)drain_at=tickGetCount();
  if(!last_status||elapsed(last_status,1000000)){
   send_status(fd,&peer,stage==DRAINING?2:tx.failed?3:1);last_status=tickGetCount();
  }
  if(tx.base!=progress_base){progress_base=tx.base;progress_at=tickGetCount();}
  if(r_pending(&tx)&&elapsed(progress_at,15000000)){stage=DRAIN_FAILED;send_status(fd,&peer,3);goto done;}
  if(!r_pending(&tx))progress_at=tickGetCount();
  if(tx.failed){stage=RETRY_FAILED;send_status(fd,&peer,3);goto done;}
  if(drain_requested&&!r_pending(&tx)&&(stage==READY||stage==DRAINING)){
   stage=DRAINING;
   if(!last_fin||elapsed(last_fin,300000)){
    if(fin_attempts++>=6){stage=DRAIN_FAILED;send_status(fd,&peer,3);goto done;}
    send_status(fd,&peer,4);
    r_wire(packet,R_FIN,1,twl?1:0,session,session_hi,tx.next,0,0,false,NULL);
    if(sendto(fd,packet,96,0,(struct sockaddr*)&peer,sizeof(peer))!=96)send_errors++;
    last_fin=tickGetCount();
   }
  }
  if(drain_at&&elapsed(drain_at,8000000)){stage=DRAIN_FAILED;send_status(fd,&peer,3);goto done;}
  threadSleep(2000);
 }
stopped:
 stage=STOPPED;
done:
 if(fd>=0)closesocket(fd);
 if(initialized)Wifi_DisconnectAP();
 IrqState done_irq=irqLock();worker_done=1;irqUnlock(done_irq);
 return 0;
}
static void sample(uint32_t buttons){
 if(captured>=RECORDS){streaming=false;drain_requested=1;snprintf(message,sizeof(message),"Captured600; draining ACKs. Wait COMPLETE.");return;}
 IrqState irq=irqLock();
 if(!offline&&(r_pending(&tx)>=32||tx.failed)){tx.backpressure++;irqUnlock(irq);return;}
 controlled[0]=0x44534931u;controlled[1]=captured;controlled[2]=buttons;controlled[3]=captured^buttons^0xA5A55A5Au;
 uint8_t*p=capture[captured];uint32_t words[4];u64 t=tickGetCount();
 for(unsigned i=0;i<4;i++)words[i]=controlled[i];
 last_read_ticks=(uint32_t)(tickGetCount()-t);
 wire_sample(p,1,twl?1:0,session,sequence,frame,last_read_ticks,0,(uint32_t)(uintptr_t)controlled,words);
 if(offline||r_offer(&tx,p,now_ms())){captured++;sequence++;}
 irqUnlock(irq);
}
static bool mount_sd(void){
 if(!fs_ready)fs_ready=fatInitDefault();
 struct stat s;return fs_ready&&stat("sd:/",&s)==0&&S_ISDIR(s.st_mode);
}
static void load_config(void){
 if(!mount_sd())return;
 FILE*cfg=fopen("sd:/DSiRABridge_032/receiver.cfg","r");if(!cfg)return;
 char line[96];if(fgets(line,sizeof(line),cfg)){
  unsigned a,b,c,d,p,r;
  char tail;
  if(sscanf(line,"%u.%u.%u.%u %u %u %c",&a,&b,&c,&d,&p,&r,&tail)==6&&a<=255&&b<=255&&c<=255&&d<=255&&p>=1024&&p<=65535&&r>=1&&r<=30){
   uint8_t old[4];memcpy(old,ip,4);ip[0]=a;ip[1]=b;ip[2]=c;ip[3]=d;
   if(private_ip()){port=p;rate=r;}else memcpy(ip,old,4);
  }
 }
 fclose(cfg);
}
static void export_capture(void){
 if(!worker_done){snprintf(message,sizeof(message),"B stop first; wait STOPPED then X.");return;}
 if(!captured){snprintf(message,sizeof(message),"No snapshots collected.");return;}
 if(!mount_sd()){snprintf(message,sizeof(message),"sd:/ unavailable; no other volume used.");return;}
 const char*dir="sd:/DSiRABridge_032";struct stat s;
 if(mkdir(dir,0777)&&errno!=EEXIST){snprintf(message,sizeof(message),"Directory create failed.");return;}
 if(stat(dir,&s)||!S_ISDIR(s.st_mode)){snprintf(message,sizeof(message),"Invalid project directory.");return;}
 int fd=-1;char dest[80];
 for(unsigned i=0;i<1000;i++){snprintf(dest,sizeof(dest),"%s/NET%03u.drb",dir,i);fd=open(dest,O_WRONLY|O_CREAT|O_EXCL,0666);if(fd>=0)break;if(errno!=EEXIST)break;}
 if(fd<0){snprintf(message,sizeof(message),"Cannot create NEW capture.");return;}
 unsigned done=0,total=captured*64;
 while(done<total){int n=write(fd,((uint8_t*)capture)+done,total-done);if(n<=0)break;done+=(unsigned)n;}
 int rc=close(fd);
 if(done==total&&rc==0){
  /* A separate, exclusive file exposes application send calls, not Wi-Fi frames. */
  char meta[80];snprintf(meta,sizeof(meta),"%s",dest);char*ext=strrchr(meta,'.');if(ext)strcpy(ext,".json");
  int mfd=open(meta,O_WRONLY|O_CREAT|O_EXCL,0666);bool meta_ok=false;
  if(mfd>=0){
   FILE*m=fdopen(mfd,"w");if(m){
    int status=fprintf(m,"{\"version\":\"0.3.2\",\"session\":%lu,\"sessionHi\":%lu,"
     "\"configuredHz\":%u,\"captured\":%lu,\"offline\":%s,\"queued\":%lu,\"originalAttempts\":%lu,"
     "\"originalAccepted\":%lu,\"retryAttempts\":%lu,\"retryAccepted\":%lu,\"sendFailed\":%lu,"
     "\"acked\":%lu,\"unacked\":%lu,\"queuePeak\":%lu,\"backpressure\":%lu,\"exhausted\":%lu,"
     "\"ackRx\":%lu,\"ackDuplicate\":%lu,\"ackLate\":%lu,\"ackInvalid\":%lu,"
     "\"rtoMs\":%lu,\"srttMs\":%lu,\"captureToAckMaxMs\":%lu,\"stage\":%d,"
     "\"attemptsMeaning\":\"0=no send;1=original;2..6=selective retransmissions\",\"txAttempts\":\"",
     (unsigned long)session,(unsigned long)session_hi,rate,(unsigned long)captured,offline?"true":"false",
     (unsigned long)tx.queued,(unsigned long)tx.original_attempts,(unsigned long)tx.original_accepted,
     (unsigned long)tx.retry_attempts,(unsigned long)tx.retry_accepted,(unsigned long)tx.send_failed,
     (unsigned long)tx.acked,(unsigned long)r_pending(&tx),(unsigned long)tx.peak,(unsigned long)tx.backpressure,
     (unsigned long)tx.exhausted,(unsigned long)tx.ack_rx,(unsigned long)tx.ack_duplicate,
     (unsigned long)tx.ack_late,(unsigned long)tx.ack_invalid,(unsigned long)tx.rto,
     (unsigned long)tx.srtt,(unsigned long)tx.capture_ack_max,stage);
    for(unsigned j=0;j<captured;j++)if(fputc('0'+tx_outcome[j],m)==EOF)status=-1;
    if(fputs("\",\"officialSubmitted\":0}\n",m)==EOF)status=-1;
    int failed=ferror(m);int closed=fclose(m);meta_ok=status>=0&&!failed&&closed==0;
   }else close(mfd);
  }
  snprintf(message,sizeof(message),meta_ok?"Saved DRB + sender JSON (%u bytes DRB).":"DRB saved (%u bytes); JSON FAILED.",done);
 }else snprintf(message,sizeof(message),"PARTIAL export: %u bytes.",done);
}
int main(void){
 consoleDemoInit();twl=isDSiMode();session=(uint32_t)tickGetCount();load_config();
 while(pmMainLoop()){
  swiWaitForVBlank();scanKeys();frame++;
  uint32_t down=keysDown(),held=keysHeld();
  if(worker_started&&worker_done){threadJoin(&worker);worker_started=false;}
  if(down&KEY_START){stop_requested=1;streaming=false;if(!exiting){exiting=true;exit_at=tickGetCount();}}
  if(exiting){if(worker_done||elapsed(exit_at,2000000))break;continue;}
  if(down&KEY_B){streaming=false;drain_requested=1;if(offline)stage=STOPPED;}
  if((down&KEY_Y)&&worker_done&&private_ip()){
   stop_requested=0;drain_requested=0;worker_done=0;offline=false;streaming=false;session_hi=(uint32_t)time(NULL);
   session=(uint32_t)tickGetCount()^(frame<<16)^(session+1);if(!session&&!session_hi)session=1;sequence=0;captured=0;
   sent=send_errors=overflows=peer_replies=0;r_init(&tx,0);memset(tx_outcome,0,sizeof(tx_outcome));
   hello_attempts=pong_attempts=ack_received=ping_received=ignored_controls=0;sample_phase=0;started_at=tickGetCount();
   threadPrepare(&worker,network_worker,NULL,worker_stack+sizeof(worker_stack),MAIN_THREAD_PRIO+1);
   threadAttachLocalStorage(&worker,NULL);worker_started=true;threadStart(&worker);
  }
  if(stage==INITIALIZING&&elapsed(started_at,20000000)){stop_requested=1;snprintf(message,sizeof(message),"INIT timeout. START exits; driver unverified.");}
  if((down&KEY_R)&&worker_done){
   offline=!offline;streaming=offline;
   if(offline){drain_requested=0;session++;sequence=0;captured=0;overflows=0;memset(&tx,0,sizeof(tx));memset(tx_outcome,0,sizeof(tx_outcome));sample_phase=0;
    hello_attempts=pong_attempts=ack_received=ping_received=ignored_controls=0;}
   snprintf(message,sizeof(message),offline?"OFFLINE capture; no radio. B pause, X export.":"Offline mode stopped.");
  }
  if((down&KEY_A)&&((stage==READY&&!drain_requested&&!worker_done)||(offline&&worker_done)))streaming=!streaming;
  if(down&KEY_X){streaming=false;export_capture();}
  if(worker_done){
   if(down&KEY_LEFT)field=(field+5)%6;
   if(down&KEY_RIGHT)field=(field+1)%6;
   int delta=(down&KEY_UP)?1:(down&KEY_DOWN)?-1:0;
   if(field<4&&delta)ip[field]=(uint8_t)(ip[field]+delta);
   if(field==4&&delta)port=(unsigned)((int)port+delta);
   if(port<1024)port=1024;
   if(port>65535)port=65535;
   if(field==5&&delta)rate=(unsigned)((int)rate+delta);
   if(rate<1)rate=1;
   if(rate>30)rate=30;
  }
  if(streaming&&((stage==READY&&!worker_done)||(offline&&worker_done))){
   sample_phase+=rate;if(sample_phase>=60){sample_phase-=60;sample(held);}
  }
  if(frame%10==0||down){
   iprintf("\x1b[2JDSi RA Bridge Network 0.3.2\nCONTROLLED DATA / NO RA SUBMISSIONS\n");
   iprintf("Mode %s; %s\n",twl?"DSi":"DS",offline?"OFFLINE":"NETWORK");
   iprintf("State %s; profiles %u\n",stages[stage],saved_profiles);
   iprintf("PC %u.%u.%u.%u:%u\n",ip[0],ip[1],ip[2],ip[3],port);
   iprintf("DS IP %s\n",local_ip);
   iprintf("Edit field %u (IP,port,Hz)\nRate %u Hz; private IP %s\n",field+1,rate,private_ip()?"YES":"NO");
   iprintf("Session %lu / frame %lu\n",(unsigned long)session,(unsigned long)frame);
   iprintf("Stored %lu/600; sent %lu\n",(unsigned long)captured,(unsigned long)sent);
   iprintf("Send errors %lu; pending %lu\n",(unsigned long)send_errors,(unsigned long)r_pending(&tx));
   iprintf("ACKed %lu; retries %lu\n",(unsigned long)tx.acked,(unsigned long)tx.retry_attempts);
   iprintf("Peer replies %lu; read %lu ticks\n",(unsigned long)peer_replies,(unsigned long)last_read_ticks);
   iprintf("Y connect | R offline | A stream\nB drain | X SD export | START exit\nD-pad edits only while stopped\n\n%s\n",message);
  }
 }
 return 0;
}
