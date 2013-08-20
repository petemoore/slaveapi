slaveapi
========

How to add new actions
----------------------
If you're creating a new action that doesn't require any new data gathering or other support code, the process is as follows:
* Create a new action in slaveapi/actions. Your action can make use of any of the clients in slaveapi/clients if desired/helpful.
* Create a new endpoint that makes use of your action.
** Actions that generally take more than a short amount of time to run should be pushed onto the work queue. Actions that are generally quick may wait on a result before returning. slaveapi/web/slave.py has examples of both.
** Your endpoint should generally accept at least GET and POST. POSTs should be used to accept new action requests. GETs will look up the status of existing actions, generally by requestid.
* Hook your endpoint up to the application in slaveapi/web/__init__.py.

If SlaveAPI doesn't already gather the information you need to do create your action, you may need to touch some of the client code (eg, if you need extra information from Inventory) or the Slave class (eg, if you need to compute new things from existing data).
