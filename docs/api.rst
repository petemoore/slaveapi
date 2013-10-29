=========
Endpoints
=========

/results
========
.. autoclass:: slaveapi.web.results.Results
    :members: get


/slaves/:slave/actions/reboot
===========================
.. autoclass:: slaveapi.web.slave.Reboot
    :members: post, get

    For details on how reboots are performed, see the documentation for
    :py:func:`slaveapi.actions.reboot.reboot`.
