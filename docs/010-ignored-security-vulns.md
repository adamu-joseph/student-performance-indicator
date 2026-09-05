# Ignored security findings: Click

This project currently pins `click==8.2.1` in [requirements.txt](../requirements.txt), but `pip-audit` still reports a Click advisory as ignored.

## Why the report is being ignored

The key reason is that the project also depends on `zenml==0.96.3`, and `zenml` depends on a lower version of `click` in its dependency tree. In other words, the vulnerability scan is seeing a package version that is present in the environment, but the project is constrained by an upstream dependency relationship that does not currently allow a clean upgrade to the patched Click version.

This means the finding is not a direct application-level bug in this repository. It is a dependency-resolution issue: the project environment includes a Click version that is flagged by the advisory, while the ZenML package set still expects an older Click release.

## Why this is intentionally documented as ignored

We do not currently change the dependency graph in a way that would break the ML stack. The practical options are:

1. Upgrade Click to a patched release, which conflicts with the version range required by ZenML.
2. Upgrade or downgrade ZenML to a compatible release, which is an upstream change outside the scope of this project’s current implementation.
3. Keep the current dependency state and record the advisory as an accepted upstream constraint until the dependency ecosystem is updated.

Because `zenml` depends on a lower version of `click`, the audit result is treated as a known dependency constraint rather than a code issue we can fix safely in this repository alone.

## Project position

This advisory is currently documented as ignored because:

- the issue is caused by the upstream package relationship between ZenML and Click,
- the repository does not directly own the transitive dependency versioning,
- and a change to Click here would likely break the project’s ZenML-based workflow.

The repository should revisit this finding when ZenML publishes a compatible Click version or when the project dependency stack is intentionally upgraded.

## Reference

- `click==8.2.1` is explicitly pinned in [requirements.txt](../requirements.txt)
- `zenml==0.96.3` is also present in [requirements.txt](../requirements.txt)
- the current project position is to treat this as an upstream dependency constraint until the toolchain is updated
