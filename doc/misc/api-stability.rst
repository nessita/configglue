=============
API stability
=============

:doc:`The release of configglue 1.0 </releases/1.0>` comes with a promise of API
stability and forwards-compatibility. In a nutshell, this means that code you
develop against configglue 1.0 will continue to work against 1.1 unchanged, and you
should need to make only minor changes for any 1.X release.

What "stable" means
===================

In this context, stable means:

   - All the public APIs -- everything documented in the linked documents below,
     and all methods that don't begin with an underscore -- will not be moved or
     renamed without providing backwards-compatible aliases.

   - If new features are added to these APIs -- which is quite possible --
     they will not break or change the meaning of existing methods. In other
     words, "stable" does not (necessarily) mean "complete."

   - If, for some reason, an API declared stable must be removed or replaced, it
     will be declared deprecated but will remain in the API for at least two
     minor version releases. Warnings will be issued when the deprecated method
     is called.

   - We'll only break backwards compatibility of these APIs if a bug or
     security hole makes it completely unavoidable.

Stable APIs
===========

In general, everything covered in the documentation is considered stable as
of 1.0.

Exceptions
==========

There are a few exceptions to this stability and backwards-compatibility
promise.

Security fixes
--------------

If we become aware of a security problem we'll do everything necessary to
fix it. This might mean breaking backwards compatibility; security trumps the
compatibility guarantee.

APIs marked as internal
-----------------------

Certain APIs are explicitly marked as "internal" in a couple of ways:

    - Some documentation may refer to internals and mention them as such. If the
      documentation says that something is internal, we reserve the right to
      change it.

    - Functions, methods, and other objects prefixed by a leading underscore
      (``_``). This is the standard Python way of indicating that something is
      private; if any method starts with a single ``_``, it's an internal API.

