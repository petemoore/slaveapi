===
API
===

---------
Endpoints
---------
/results
========
.. autoclass:: slaveapi.web.results.Results
    :members: get


/slaves/:slave/actions/reboot
=============================
.. autoclass:: slaveapi.web.slave.Reboot


/slaves/:slave/actions/shutdown_buildslave
==========================================
.. autoclass:: slaveapi.web.slave.ShutdownBuildslave


-------
Helpers
-------
ActionView
==========
.. autoclass:: slaveapi.web.action_base.ActionView
    :members: get, post
