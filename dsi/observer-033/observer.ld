OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(observer_entry)
SECTIONS {
 . = 0x02200000;
 .header : { KEEP(*(.observer.header)) }
 .text : { KEEP(*(.text.entry)) *(.text*) *(.rodata*) }
 .data : { *(.data*) *(.got*) }
 .bss : { *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.comment*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
 ASSERT(SIZEOF(.header)==64,"Bad observer header")
 ASSERT(.<=0x02201000,"Observer code exceeds reserved page")
 ASSERT(SIZEOF(.data)==0 && SIZEOF(.bss)==0,"Observer must be self-contained")
}
