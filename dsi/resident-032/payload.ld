OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(payload_entry)
SECTIONS {
 . = 0;
 .text : { KEEP(*(.text.entry)) *(.text*) *(.rodata*) }
 .data : { *(.data*) *(.got*) }
 .bss : { *(.bss*) *(COMMON) }
 /DISCARD/ : { *(.comment*) *(.note*) *(.ARM.exidx*) *(.ARM.extab*) }
 ASSERT(SIZEOF(.text) <= 4096, "Payload too large")
 ASSERT(SIZEOF(.data) == 0, "Payload must not have absolute data/GOT")
 ASSERT(SIZEOF(.bss) == 0, "Payload must not have absolute BSS")
}
