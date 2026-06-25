🦀 Tip of the day 44 follow-up

Follow-up questions from the discussion on [Tip 44: Editions, Releases, and Who Keeps the Promise](44-editions-releases.md).

## Mixing editions looks clean on paper, but C++ tried something similar and it broke down. Instantiate a template designed in one language version with types from another, in a third translation context, and you get contradictions. How does Rust avoid that? Are the changes simply smaller in scope, or is the entanglement between code units lower?

Both, but the deeper answer is that Rust forbids the entire class of problem rather than trying to make it consistent.

An edition is deliberately narrow. It changes only how a crate's own source is read, never what the compiled program means. Editions touch the front end alone: lexing, parsing, name resolution, and a few desugarings. By the time code reaches the type system, trait resolution, and codegen, it has been normalized into one edition-independent representation. At that level editions no longer exist, so two editions can never disagree about a type or a trait. The backend is the same for everyone.

That is not a happy accident, it is a hard rule. An edition change is only allowed if it is invisible across crate boundaries. Anything that would alter cross-crate semantics, such as trait resolution, type layout, or instantiation behavior, is not eligible to ship as an edition change in the first place. The rule has been there since editions were introduced, so the dangerous category of change you describe simply has nowhere to live.

This is the difference from the C++ situation. C++ tried to make instantiation-context-dependent semantics consistent across versions. Rust does not reconcile them, it rules them out.

## Following from that: what happens to generics? If a generic is written in one edition, the type it is instantiated with comes from a second edition, and the instantiation site sits in a third, which edition wins?

None of them competes, because each edition governs only its own crate's source.

A generic is type-checked once, in its home crate, under its home edition, and its meaning is frozen there. Monomorphization is just substitution into already-checked IR. The instantiation site never re-interprets the body of the generic.

So a generic from edition A, a type from edition B, and an instantiation site in edition C all coexist with no conflict. Each was read and checked under its own edition while it was still source, and they only ever meet later as edition-independent IR. There is no "winning" edition because by the point they interact, the concept of an edition is gone.

## Does the promise still hold for something genuinely entangled, like one crate running macros over another crate's code? Is that even a meaningful scenario?

It is meaningful, and it holds, because edition is tracked per span rather than per expansion.

Every token carries the edition of the crate it came from, and the compiler interprets each token under that edition. There is no single "expansion edition" that the compiler has to pick when a macro defined in one crate is invoked in another. The macro's own tokens are read under the macro's edition, and the caller's tokens are read under the caller's edition, even though they end up woven into the same expansion.

The classic illustration is `await`, which became a reserved keyword in edition 2018. A macro defined in a 2015 crate can use `await` as an ordinary identifier, and that macro keeps compiling when it is invoked from a 2018 or later crate where `await` is a keyword:

```rust
// in a 2015-edition crate: `await` is just an identifier here
#[macro_export]
macro_rules! poll_once {
    ($fut:expr) => {{
        let await = $fut; // legal: 2015 tokens are read as 2015
        await
    }};
}
```

```rust
// in a 2024-edition crate: `await` is a keyword here, but the macro still works
let value = poll_once!(some_future);
```

The macro's tokens stay 2015 and the call site's tokens stay 2024. Neither edition has to bend to the other, so the promise survives even the entangled case.
