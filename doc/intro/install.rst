Quick install guide
===================

Install configglue
------------------

You've got three easy options to install configglue:

    * Install a version of configglue :doc:`provided by your operating system
      distribution </misc/distributions>`. This is the quickest option for those
      who have operating systems that distribute configglue.

    * :ref:`Install an official release <installing-official-release>`. This
      is the best approach for users who want a stable version number and aren't
      concerned about running a slightly older version of configglue.

    * :ref:`Install the latest development version
      <installing-development-version>`. This is best for users who want the
      latest-and-greatest features and aren't afraid of running brand-new code.

.. admonition:: Always refer to the documentation that corresponds to the
    version of configglue you're using!

    If you do either of the first two steps, keep an eye out for parts of the
    documentation marked **new in development version**. That phrase flags
    features that are only available in development versions of configglue, and
    they likely won't work with an official release.


Verifying
---------

To verify that configglue can be seen by Python, type ``python`` from your shell.
Then at the Python prompt, try to import configglue::

    >>> import configglue
    >>> print configglue.__version__
    |version|


That's it!
----------

That's it -- you can now :doc:`move onto the quickstart guide </intro/quickstart>`.

