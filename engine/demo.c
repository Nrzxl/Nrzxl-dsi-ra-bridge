/* Controlled local rcheevos demo, MIT. No rc_client, login or HTTP. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "rc_runtime.h"
#include "rc_error.h"
static uint8_t memory[16];
static unsigned triggered;
static uint32_t RC_CCONV peek(uint32_t addr,uint32_t n,void *ud) {
    (void)ud;
    if(!n || n>4 || addr>sizeof(memory) || n>sizeof(memory)-addr) return 0;
    uint32_t value=0;for(uint32_t i=0;i<n;i++)value|=(uint32_t)memory[addr+i]<<(8*i);
    return value;
}
static void RC_CCONV event(const rc_runtime_event_t *ev) {
    if(ev->type==RC_RUNTIME_EVENT_ACHIEVEMENT_TRIGGERED){
        triggered++;printf("LOCAL_TEST_TRIGGER id=%u; NOT SUBMITTED\n",ev->id);
    }
}
int main(void) {
    rc_runtime_t rt;rc_runtime_init(&rt);
    int a=rc_runtime_activate_achievement(&rt,1,"0xH000004=3",NULL,0);
    int b=rc_runtime_activate_achievement(&rt,2,"M:0xH000004=5",NULL,0);
    if(a!=RC_OK || b!=RC_OK) {
        fprintf(stderr,"Definition error %d/%d\n",a,b);rc_runtime_destroy(&rt);return 1;
    }
    rc_runtime_do_frame(&rt,event,peek,NULL,NULL);
    for(unsigned n=1;n<=5;n++){
        memory[4]=(uint8_t)n;rc_runtime_do_frame(&rt,event,peek,NULL,NULL);
        unsigned value=0,target=0;
        rc_runtime_get_achievement_measured(&rt,2,&value,&target);
        printf("LOCAL_TEST_PROGRESS %u/%u\n",value,target);
    }
    rc_runtime_destroy(&rt);
    if(triggered!=2){fprintf(stderr,"Expected 2 triggers, got %u\n",triggered);return 1;}
    puts("PASS: controlled runtime only; zero official unlock requests.");
    return 0;
}
