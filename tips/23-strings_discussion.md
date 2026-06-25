🦀 Tip of the day 23 follow-up

Follow-up questions from the discussion on [Tip 23: Strings, or Why There Are Two of Them](23-strings.md).

## When you write `let slice = &s[0..3]`, is the range counted in bytes or in characters, and why?

It is bytes. String slicing in Rust indexes the underlying UTF-8 byte buffer, not characters.

The reason goes back to how `str` is stored. A `str` is just a run of bytes that happens to be valid UTF-8, and a `&str` is a fat pointer carrying an address and a byte length. There is no per-character index sitting alongside the bytes, so the only number Rust can use for slicing in constant time is a byte offset. Counting characters would mean walking the string from the start every time, which is exactly the cost Rust refuses to hide from you.

So `0..3` means "the first three bytes," and how many characters that covers depends on the content:

```rust
let s = "héllo";
let slice = &s[0..3]; // "hé"
```

That slice is three bytes but only two characters. The `é` is U+00E9, which UTF-8 encodes as two bytes, so `h` (1 byte) plus `é` (2 bytes) fills the `0..3` range exactly.

The catch is that a byte range has to land on character boundaries. If a range starts or ends in the middle of a multi-byte character, the slice does not silently hand you half a character. It panics:

```rust
let r = "🦀 hi";
let bad = &r[0..2]; // panics
```

The panic message tells you precisely what went wrong:

```text
byte index 2 is not a char boundary; it is inside '🦀' (bytes 0..4) of `🦀 hi`
```

The crab is four bytes, so the only valid byte offsets at the front of that string are 0 and 4. Asking for `0..2` cuts the character in half, and rather than return malformed UTF-8, Rust stops.

This is the same honesty the tip is built around. Bytes and characters are different things, and Rust makes you say which one you mean. If you actually want character positions, iterate with `s.chars()` and pay the linear cost on purpose. If you want a byte slice, use a byte range and accept that it must align to a character boundary.
