slaveapi
========

How to add new endpoints:
* Create a new action in slaveapi/actions. Your action can make use of any of the clients in slaveapi/clients if desired/helpful.
* Create a new endpoint that makes use of your action.
** Actions that generally take more than a short amount of time to run should be pushed onto the work queue. Actions that are generally quick may wait on a result before returning. slaveapi/web/slave.py has examples of both.
** Your endpoint should generally accept at least GET and POST. POSTs should be used to accept new action requests. GETs will look up the status of existing actions, generally by requestid.
* Hook your endpoint up to the application in slaveapi/web/__init__.py.
