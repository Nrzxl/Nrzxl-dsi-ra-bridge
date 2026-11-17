# Cooperative monitor specimen; persistent injection BLOCKED
The diagnostic's main loop updates its own four-word "game" state once per
VBlank and captures it into a 600-record buffer. This is deliberately a
cooperative specimen, not a resident hook in another title.
It models bounded reads, frame numbering, buffer exhaustion and export at a
safe pause. It does not prove arbitrary DS game persistence.

A homebrew title launched via nds-bootstrap-hb does not get the retail CE9/CE7
hooks. A retail bootstrap patch cannot be proven by loading this homebrew.
Next stage must use an isolated fork, linker/map reservation, CE7 VBlank
counter and an ARM9 hook with an explicit stack/cache contract. No patched
bootstrap binary is supplied in 0.1.0.
