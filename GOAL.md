# Goal

Native Zephyr tensor/autograd stack sufficient to train, evaluate, checkpoint,
resume and generate from this project's models with no Python or libtorch in
the execution path, plus a fairly controlled test of the phase-reasoner
architecture.

Specification: `../zephyr-ml-phase-reasoner-spec-2026-09-21/`, version
2026-09-21. `MASTER_PLAN.md` there is authoritative for milestone order,
`agent/ACCEPTANCE_TESTS.md` for what counts as evidence. Nothing in that
package is a delivered implementation; every acceptance ID starts unmet.

## Two success axes, deliberately independent

1. **Zephyr numerical and compiler correctness.** A working tensor stack is
   valuable whatever the phase model does.
2. **Scientific value of the phase architecture.** A negative result here does
   not invalidate axis 1, and a working reference model does not validate the
   backend.

Do not let either hold the other hostage. In particular the scientific
question is answerable in Python long before the native stack exists, and
should be.

## Out of scope

Full PyTorch API parity. Reimplementing cuBLAS. Distributed training. A Python
compatibility layer. Arbitrary-program differentiation. Any claim about
quantum computation or consciousness — the model is classical, and its complex
state is exactly 2D real numbers, so the representation alone cannot confer an
expressivity advantage.

## Current position

M0 complete, M1b delegated, M2a next. See `.agent/task.md` for the resumable
record and `RESULTS.md` for measurements.
