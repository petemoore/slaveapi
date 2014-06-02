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

/slaves/:slave/actions/buildslave_last_activity
===============================================
.. autoclass:: slaveapi.web.slave.GetLastActivity

/slaves/:slave/actions/buildslave_uptime
===========================================
.. autoclass:: slaveapi.web.slave.GetUptime

/slaves/:slave/actions/reboot
=============================
.. autoclass:: slaveapi.web.slave.Reboot


/slaves/:slave/actions/shutdown_buildslave
==========================================
.. autoclass:: slaveapi.web.slave.ShutdownBuildslave

/slaves/:slave/actions/disable
==========================================
.. autoclass:: slaveapi.web.slave.Disable

-------
Helpers
-------
ActionView
==========
.. autoclass:: slaveapi.web.action_base.ActionView
    :members: get, post
