/* Original MIT. IRQ interposer. The displaced instruction must be verified push{r4,lr}. */
.syntax unified
.arm
.section .observer.header,"a"
.global observer_header
observer_header:
 .ascii "DSIOBS33"
 .word 1,64,20,0,0,0,0x02203000,32,1200,0x02202000,0x0221C000,0x02220000,0xE92D4010,0
.section .text.entry,"ax"
.global observer_entry
.type observer_entry,%function
observer_entry:
 push {r0-r12,lr}
 mrs r0,cpsr
 push {r0,r1}
 mov r4,sp
 ldr sp,=0x02220000
 push {r4,lr}
 bl observer_sample
 pop {r4,lr}
 mov sp,r4
 pop {r0,r1}
 msr cpsr_f,r0
 pop {r0-r12,lr}
 /* Execute displaced original push, then resume at original function+4. */
 .word 0xE92D4010
 ldr pc,observer_resume
.global observer_resume
observer_resume:
 .word 0
.size observer_entry,.-observer_entry
