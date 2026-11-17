/* CPU-only ARM946 simulation. No DS boot, BIOS, audio, Wi-Fi or IRQ timing model.
 * Program B is actual devkitARM machine code. Host monitor uses A's exact reader. */
#include <unicorn/unicorn.h>
#include "../dsi/resident-032/shared.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#define SHARED 0x02300000u
#define STACK  0x02400000u
#define RET    0x02500000u
typedef struct {unsigned instructions,frames,valid,rejected;uint32_t last_bframe;} Bench;
static void instruction(uc_engine*uc,uint64_t address,uint32_t size,void*user){
 (void)address;(void)size;Bench*b=user;
 if(++b->instructions%500)return;
 PocState s;assert(uc_mem_read(uc,SHARED,&s,sizeof(s))==UC_ERR_OK);
 PocRecord r;poc_read(&s,&r,b->frames,0);
 if(r.valid){b->valid++;assert(r.bframe>=b->last_bframe);b->last_bframe=r.bframe;}
 else b->rejected++;
 b->frames++;uint32_t next=b->frames;assert(uc_mem_write(uc,SHARED+12,&next,4)==UC_ERR_OK);
 if(b->frames==6000){uint32_t stop=1;assert(uc_mem_write(uc,SHARED+8,&stop,4)==UC_ERR_OK);}
}
int main(int argc,char**argv){
 assert(argc==2);FILE*f=fopen(argv[1],"rb");assert(f);uint8_t code[4096];size_t n=fread(code,1,sizeof(code),f);assert(feof(f)&&n>0);fclose(f);
 for(unsigned pass=0;pass<2;pass++){
  uint32_t base=pass?0x02200000u:0x02010000u;uc_engine*uc;assert(uc_open(UC_ARCH_ARM,UC_MODE_ARM,&uc)==UC_ERR_OK);
  assert(uc_ctl_set_cpu_model(uc,UC_CPU_ARM_946)==UC_ERR_OK);
  assert(uc_mem_map(uc,base,65536,UC_PROT_ALL)==UC_ERR_OK);
  assert(uc_mem_map(uc,SHARED,65536,UC_PROT_ALL)==UC_ERR_OK);
  assert(uc_mem_map(uc,STACK,65536,UC_PROT_ALL)==UC_ERR_OK);
  assert(uc_mem_map(uc,RET,4096,UC_PROT_ALL)==UC_ERR_OK);
  assert(uc_mem_write(uc,base,code,n)==UC_ERR_OK);
  PocState state={0};state.magic=POC_MAGIC;state.abi=1;state.guard=POC_GUARD;state.counter=7;state.checksum=7^0xA55A9321u;
  assert(uc_mem_write(uc,SHARED,&state,sizeof(state))==UC_ERR_OK);
  uint32_t r0=SHARED,sp=STACK+65520,lr=RET;
  assert(uc_reg_write(uc,UC_ARM_REG_R0,&r0)==UC_ERR_OK);
  assert(uc_reg_write(uc,UC_ARM_REG_SP,&sp)==UC_ERR_OK);assert(uc_reg_write(uc,UC_ARM_REG_LR,&lr)==UC_ERR_OK);
  Bench b={0};uc_hook hook;assert(uc_hook_add(uc,&hook,UC_HOOK_CODE,instruction,&b,base,base+n)==UC_ERR_OK);
  uc_err err=uc_emu_start(uc,base,RET,10000000,10000000);
  if(err)fprintf(stderr,"Unicorn: %s\n",uc_strerror(err));assert(err==UC_ERR_OK);
  assert(b.frames==6000&&b.valid>5000&&b.last_bframe>5900);
  assert(uc_mem_read(uc,SHARED,&state,sizeof(state))==UC_ERR_OK);assert(state.guard==POC_GUARD&&state.stop);
  printf("{\"status\":\"PASS\",\"scope\":\"ARM946 CPU-only; simulated resident frame hook\","
   "\"loadBase\":%u,\"frames\":%u,\"valid\":%u,\"tornRejected\":%u,\"instructions\":%u,\"physical\":\"NOT_RUN\"}\n",
   base,b.frames,b.valid,b.rejected,b.instructions);
  uc_close(uc);
 }
 PocState torn={0};torn.magic=POC_MAGIC;torn.abi=1;torn.guard=POC_GUARD;torn.generation=1;
 PocRecord rec;poc_read(&torn,&rec,0,0);assert(!rec.valid);
 return 0;
}
