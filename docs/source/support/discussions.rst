Troubleshooting & Discussions
==============================

As part of the Registry Users community you can use and contribute to the `discussion forum <https://github.com/NASA-PDS/registry/discussions>`_ hosted on github.

Here is a list of common, issues:

FIPS mode
**********

If harvest or registry manager returns the following error:

.. code-block:: bash

    FIPS mode: only SunJSSE TrustManagers may be used

This means your system has FIPS mode turned on. This is not supported by our OpenSearch database serverside as it restricts harvest and registry-mgr to using only FIPS-approved cryptographic algorithms and other security functions to communicate with it.

To turn the FIPS mode off for your harvest or registry-mgr session, in the same terminal, just run:

.. code-block:: bash

    export JDK_JAVA_OPTIONS='-Dcom.redhat.fips=false'

Then, run harvest or registry-mgr, as usual.


*(See `harvest#247 <https://github.com/NASA-PDS/harvest/issues/247>`_ for details)*
