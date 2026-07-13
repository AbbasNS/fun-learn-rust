🦀 Tip of the day 47 follow-up

Follow-up questions from the discussion on [Tip 47: Cross-Compilation and Targets](47-cross-compilation.md).

## Which types depend on the target, and which are the same everywhere?

Almost nothing about Rust's primitive types depends on the target, which is a deliberate break from C. The fixed-width types are exactly their stated width on every platform: `i8`/`u8` are 8 bits, `i16`/`u16` are 16, `i32`/`u32` are 32, `i64`/`u64` are 64, `i128`/`u128` are 128. `bool` is one byte, `f32` is 32 bits, `f64` is 64. So `i32` is 32 bits no matter what you build for.

`char` is also fixed: it is always 4 bytes on every target. A Rust `char` is a Unicode scalar value, not a C character, so its width has nothing to do with the machine. In C, by contrast, `int` might be 16 or 32 bits, `long` is 32 on Windows but 64 on 64-bit Linux, and even `char` is not guaranteed to be 8 bits. Rust pinned all of that down.

What does vary with the target:

- `usize` and `isize`: pointer-sized integers. This is the main one. They are 64 bits on a 64-bit target, 32 on a 32-bit target, 16 on a 16-bit target. They are the types for indexing, `.len()`, and pointer offsets.
- Raw pointers and references: for a thin pointer (`&T` or `*const T` where `T` is `Sized`) the size follows the address width, the same as `usize`. Pointers to unsized types are fat, two words wide: `&[T]` and `&str` carry a length, and `&dyn Trait` carries a vtable pointer, so they are twice the size of `usize`.
- The C FFI types (`std::ffi::c_int`, `c_long`, and friends): these mirror the platform C ABI on purpose, so `c_long` is 32 bits on Windows and 64 bits on 64-bit Linux.
- Endianness: little-endian or big-endian byte order. Most targets are little-endian.
- Alignment, though not size: a fixed-width type keeps its size but can change alignment. Some 32-bit targets, for example, align `u64` to 4 bytes even though it is still 8 bytes wide.
- Availability of some features: `AtomicU64`, for instance, does not exist on targets without 64-bit atomics.

## What happens on a small target that only supports 16-bit integers natively?

Think of a microcontroller like MSP430, or AVR (an 8-bit core with 16-bit addresses). `i32` is still exactly 32 bits there. The CPU cannot do 32-bit arithmetic in one instruction, so the compiler synthesizes it from several 16-bit or 8-bit operations. The result is correct, just larger and slower code. The same holds all the way up: `i64` and `i128` work too, emulated in software.

What actually changes is `usize`. It becomes 16 bits, matching the pointer width. The practical consequence is a ceiling on collection sizes. A single allocation is capped at `isize::MAX` bytes (pointer offsets go through a signed integer), and a slice or `Vec` is bounded by that. On a 16-bit target `isize::MAX` is 32767, so a `Vec<u8>` tops out at 32767 bytes, and a wider element type at `isize::MAX / size_of::<T>()` elements. `usize::MAX` itself is 65535, but only a `Vec` of zero-sized types can reach that. The width of `usize` follows how far the machine can address, not how wide its arithmetic unit is.

## And the opposite: a target where the smallest addressable unit is 32 bits?

That describes a word-addressed machine, like some DSPs, where C's `CHAR_BIT` is 32 and an 8-bit integer type does not exist. Rust does not run there. Its memory model hard-codes an 8-bit byte: `u8` is defined as 8 bits and memory is byte-addressable, with no `CHAR_BIT`-style setting to change it. Rust simply has no target for hardware that cannot address 8-bit units.

This is the flip side of the earlier guarantees. Rust buys portability by refusing the exotic hardware that C stretches to accommodate. And note again that `char` being 32 bits in Rust is unrelated to any of this: it is a 4-byte Unicode scalar on every target, not a reflection of the machine word.

## Is there a way to query the most efficient integer type for a platform?

There is no direct equivalent of C's `int_fast32_t` family (a "fastest integer of at least N bits") in the standard library. The idiomatic substitutes:

- `usize` and `isize` match the pointer width, which lines up with the native register width on most mainstream targets (though not all: ILP32-on-64-bit ABIs like x86_64 x32 and arm64_32 have 32-bit pointers on a 64-bit CPU). They are the closest thing to "the efficient type," and they are what you use for indexing anyway.
- An unconstrained integer literal defaults to `i32`, chosen as a good all-round default. On essentially every real target it lives in a register and is fast.

To branch on the target at compile time, use `cfg!` or `#[cfg(...)]`:

```rust
if cfg!(target_pointer_width = "16") {
    // take the small-target path
}

#[cfg(target_endian = "big")]
fn to_wire(x: u32) -> u32 { x.swap_bytes() }
```

Useful keys include `target_pointer_width` ("16", "32", "64"), `target_arch`, `target_endian`, `target_feature`, and `target_has_atomic`. You can also read widths and sizes directly, all usable in `const` contexts:

```rust
const W: u32 = usize::BITS;                    // 16, 32, or 64
const SZ: usize = std::mem::size_of::<u64>();  // always 8
```

If you genuinely wanted a per-target "fast" alias, you would build it yourself with `cfg`:

```rust
#[cfg(target_pointer_width = "16")]
type Fast = u16;
#[cfg(not(target_pointer_width = "16"))]
type Fast = u32;
```

In practice, you reach for `usize` when indexing, a fixed-width type when the exact width matters (wire formats, hardware registers), and let the optimizer handle the rest.
