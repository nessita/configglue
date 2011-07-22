FAQ: Installation
=================

How do I get started?
---------------------

    #. `Download the code`_.
    #. Install configglue (read the :doc:`installation guide </intro/install>`).
    #. Walk through the :doc:`quickstart guide </intro/quickstart>`.
    #. Check out the rest of the :doc:`documentation </index>`, and `ask questions`_ if you
       run into trouble.

.. _`Download the code`: https://launchpad.net/configglue/+download
.. _ask questions: https://answers.launchpad.net/configglue/

What are configglue's prerequisites?
------------------------------------

configglue requires Python_, specifically any version of Python from 2.6
through 2.7. It also requires pyxdg_, for automatically finding configuration
files from standard locations, when using the provided
:class:`~configglue.app.base.App` base class.

.. _Python: http://www.python.org/
.. _pyxdg: http://www.freedesktop.org/wiki/Software/pyxdg

Can I use Django with Python 3?
-------------------------------

Not at the moment. Python 3.0 introduced a number of
backwards-incompatible changes to the Python language, and although
these changes are generally a good thing for Python's future, it will
be a while before most Python software catches up and is able to run
on Python 3.0. For configglue, the transition is expected to happen
soon, so keep around!

In the meantime, Python 2.x releases will be supported and provided
with bug fixes and security updates by the Python development team, so
continuing to use a Python 2.x release during the transition should
not present any risk.

Should I use the stable version or development version?
-------------------------------------------------------

Generally, if you're using code in production, you should be using a
stable release. The configglue project is currently in it's pre-1.0 stage,
so there are still issues being worked on that can break API compatiblity.
Once we reach 1.0, API backwards compatibility should be better guaranteed.

