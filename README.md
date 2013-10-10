slaveapi
========

Running Slaveapi
++++++++++++++++

First, copy `slaveapi.ini.sample` to `slaveapi.ini` and put it somewhere that config files belong.
Edit the file to customize your settings.
You probably want to adjust the `[server] port` and `[secrets] credentials_file` parameters, at least.

Credentials File
----------------

The credentials file should be a JSON file with the following keys:

 * `inventory` -- the password for inventory access
 * `ipmi` -- the IPMI password
 * `bugzilla` -- the Bugzilla API password
 * `ssh` -- a mapping of usernames to lists of passwords for those usernames; the passwords will be tried sequentially.

Example:
  
  {
    "inventory": "sekrit1", "ipmi": "sekrit2", "bugzilla": "sekrit3",
    "ssh": {
        "foobld": [ "new", "old", "older", "oldest" ],
        "administrator": [ "New", "Old", "Older", "Oldest" ]
    }
  }

Developing Slaveapi
+++++++++++++++++++

Setting up a Development Environment
------------------------------------

To set up a dev environment, install slaveapi into a virtualenv using `pip -e`, then copy the `slaveapi.ini` as described above.
Create `credentials.json` in the current directory as well, based on the example above, and set the path in `slaveapi.ini` to an unqualified `"credentials.json"`.
Make sure `[server] daemonize` is set to `false` in the config file, then run

  python slaveapi-server.py start slaveapi.ini

Adding New Actions
------------------
If you're creating a new action that doesn't require any new data gathering or other support code, the process is as follows:
* Create a new action in slaveapi/actions. Your action can make use of any of the clients in slaveapi/clients if desired/helpful.
* Create a new endpoint that makes use of your action.
** Actions that generally take more than a short amount of time to run should be pushed onto the work queue. Actions that are generally quick may wait on a result before returning. slaveapi/web/slave.py has examples of both.
** Your endpoint should generally accept at least GET and POST. POSTs should be used to accept new action requests. GETs will look up the status of existing actions, generally by requestid.
* Hook your endpoint up to the application in slaveapi/web/__init__.py.

If SlaveAPI doesn't already gather the information you need to do create your action, you may need to touch some of the client code (eg, if you need extra information from Inventory) or the Slave class (eg, if you need to compute new things from existing data).
