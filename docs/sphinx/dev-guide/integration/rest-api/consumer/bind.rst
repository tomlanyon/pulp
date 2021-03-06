Repository Binding
==================

.. _bind:

Bind a Consumer to a Repository
-------------------------------

Bind a :term:`consumer` to a :term:`repository's <repository>` :term:`distributor`
for the purpose of consuming published content.  Binding the consumer is performed
in the following steps:

 1. Create the :term:`binding` on server.
 2. Send a request to the consumer to create the binding.

Each step is represented by a :ref:`call_report` in the returned :ref:`call_report_list`.

The distributor may support configuration options that it may use for that particular
binding. These options would be used when generating the payload that is sent to consumers
so they may access the repository. See the individual distributor's documentation for
more information on the format.

| :method:`post`
| :path:`/v2/consumers/<consumer_id>/bindings/`
| :permission:`create`
| :param_list:`post`

* :param:`repo_id,string,unique identifier for the repository`
* :param:`distributor_id,string,identifier for the distributor`
* :param:`?options,object,options passed to the handler on the consumer`
* :param:`?notify_agent,bool,indicates if the consumer should be sent a message about the new binding; defaults to true if unspecified`
* :param:`?binding_config,object,options to be used by the distributor for this binding`

| :response_list:`_`

* :response_code:`202,if the bind request was accepted`
* :response_code:`400,if one or more of the parameters is invalid`
* :response_code:`404,if the consumer, repository or distributor does not exist`

| :return:`A` :ref:`call_report_list`

:sample_request:`_` ::

 {
   "repo_id": "test-repo",
   "distributor_id": "dist-1"
 }

.. _unbind:

Unbind a Consumer
-----------------

Remove a binding between a :term:`consumer` and a :term:`repository's <repository>` :term:`distributor`.

Unbinding the consumer is performed in the following steps:

 1. Mark the :term:`binding` as deleted on the server.
 2. Send a request to the consumer to remove the binding.
 3. Once the consumer has confirmed that the binding has been removed, it is permanently
    deleted on the server.

The steps for a forced unbind are as follows:

 1. The :term:`binding` is deleted on the server.
 2. Send a request to the consumer to remove the binding.  The result of the consumer
    request discarded.

Each step is represented by a :ref:`call_report` in the returned :ref:`call_report_list`.

| :method:`delete`
| :path:`/v2/consumers/<consumer_id>/bindings/<repo_id>/<distributor_id>`
| :permission:`delete`
| :param_list:`delete` The consumer ID, repository ID and distributor ID are included
  in the URL itself.

* :param:`?force,bool,delete the binding immediately and discontinue tracking consumer actions`
* :param:`?options,object,options passed to the handler on the consumer`

| :response_list:`_`

* :response_code:`202,the unbind request was accepted`
* :response_code:`400,if one or more of the parameters is invalid`
* :response_code:`404,if the binding does not exist`

| :return:`A` :ref:`call_report_list`



Retrieve a Single Binding
-------------------------

Retrieves information on a single binding between a consumer and a repository.

| :method:`get`
| :path:`/v2/consumers/<consumer_id>/bindings/<repo_id>/<distributor_id>`
| :permission:`read`
| :param_list:`get` None; the consumer ID, repository ID and distributor ID are included
  in the URL itself. There are no supported query parameters.
| :response_list:`_`

* :response_code:`200,if the bind exists`
* :response_code:`404,if no bind exists with the given IDs`

| :return:`database representation of the matching bind`

:sample_response:`200` ::

 {
   "repo_id": "test-repo",
   "consumer_id": "test-consumer",
   "_ns": "consumer_bindings",
   "_id": {"$oid": "5008604be13823703800003e"},
   "distributor_id": "dist-1",
   "id": "5008604be13823703800003e"
 }


Retrieve All Bindings
---------------------

Retrieves information on all bindings for the specified consumer.

| :method:`get`
| :path:`/v2/consumers/<consumer_id>/bindings/`
| :permission:`read`
| :param_list:`get` None; the consumer ID is included in the URL itself.
      There are no supported query parameters.
| :response_list:`_`

* :response_code:`200,if the consumer exists`

| :return:`a list of database representations of the matching binds`

:sample_response:`200` ::

 [
   {
     "repo_id": "test-repo",
     "consumer_id": "test-consumer",
     " _ns": "consumer_bindings",
     "_id": {"$oid": "5008604be13823703800003e"},
     "distributor_id": "dist-1",
     "id": "5008604be13823703800003e"
   },
     "repo_id": "test-repo2",
     "consumer_id": "test-consumer",
     " _ns": "consumer_bindings",
     "_id": {"$oid": "5008604be13823703800003e"},
     "distributor_id": "dist-1",
     "id": "5008604be13823703800003e"
   },
  ]


Retrieve Binding By Consumer And Repository
-------------------------------------------

Retrieves information on all bindings between a consumer and a repository.

| :method:`get`
| :path:`/v2/consumers/<consumer_id>/bindings/<repo_id>/`
| :permission:`read`
| :param_list:`get` None; the consumer and repository IDs are included
      in the URL itself. There are no supported query parameters.
| :response_list:`_`

* :response_code:`200,if the bind exists`
* :response_code:`404,if no bind exists with the given IDs`

| :return:`a database representation of the matching bind`

:sample_response:`200` ::

 {
   "repo_id": "test-repo",
   "consumer_id": "test-consumer",
   "_ns": "consumer_bindings",
   "_id": {"$oid": "5008604be13823703800003e"},
   "distributor_id": "dist-1",
   "id": "5008604be13823703800003e"
 }
