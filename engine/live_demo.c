/* MIT. rcheevos controlled-data demonstrator. stdin only; no HTTP client.
 * IDs 1/2 are LOCAL TEST IDs, not IDs from a RetroAchievements game.
 * Sampling is not frame-accurate game monitoring and cannot award achievements.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "rc_runtime.h"
#include "rc_error.h"
static uint8_t ram[16];
static uint32_t active_session;
static void RC_CCONV event(const rc_runtime_event_t* e){
 if(e->type==RC_RUNTIME_EVENT_ACHIEVEMENT_TRIGGERED){
  printf("{\"event\":\"LOCAL_TEST_TRIGGER\",\"id\":%u,\"session\":%u,\"submitted\":false}\n",e->id,active_session);
 }
}
static uint32_t RC_CCONV peek(uint32_t a,uint32_t n,void* u){
 (void)u;if(!n||n>4||a>sizeof(ram)||n>sizeof(ram)-a)return 0;
 uint32_t v=0;for(uint32_t i=0;i<n;i++)v|=(uint32_t)ram[a+i]<<(i*8);return v;
}
static int prepare(rc_runtime_t* r){
 memset(ram,0,sizeof(ram));rc_runtime_init(r);
 if(rc_runtime_activate_achievement(r,1,"0xX000004>=120",NULL,0)!=RC_OK)return 0;
 if(rc_runtime_activate_achievement(r,2,"M:0xX000004>=300",NULL,0)!=RC_OK)return 0;
 /* An explicitly synthetic false frame arms the LOCAL TEST definitions. */
 rc_runtime_do_frame(r,event,peek,NULL,NULL);return 1;
}
int main(void){
 rc_runtime_t runtime;int initialized=0;uint32_t session,seq,counter;char line[128];
 while(fgets(line,sizeof(line),stdin)){
  unsigned a,b,c;char extra;
  if(sscanf(line,"%u %u %u %c",&a,&b,&c,&extra)!=3)continue;
  session=(uint32_t)a;seq=(uint32_t)b;counter=(uint32_t)c;
  if(!initialized||session!=active_session){
   if(initialized){rc_runtime_destroy(&runtime);}
   active_session=session;
   if(!prepare(&runtime))return 2;
   initialized=1;
  }
  for(unsigned i=0;i<4;i++)ram[4+i]=(uint8_t)(counter>>(8*i));
  rc_runtime_do_frame(&runtime,event,peek,NULL,NULL);
  unsigned value=0,target=0;rc_runtime_get_achievement_measured(&runtime,2,&value,&target);
  printf("{\"event\":\"LOCAL_TEST_PROGRESS\",\"session\":%u,\"seq\":%u,\"value\":%u,\"target\":%u,\"submitted\":false}\n",session,seq,value,target);
  fflush(stdout);
 }
 if(initialized){rc_runtime_destroy(&runtime);}
 return 0;
}
