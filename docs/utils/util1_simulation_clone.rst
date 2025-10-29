Ultility 1: Clone a simulation
==============================
This example demonstrates how to clone a simulation.

Code Example
------------

The ``simulation_clone.sh`` script has been **embedded into the GINCCO_lib** package and can now be executed directly through the command-line interface.

To use it, simply navigate to the directory that contains your list of SYMPHONIE simulations and run:


.. code-block:: bash

    gincco clone --model SYMPHONIE --from GOT_REF2 --to GOT_REF5


With: 

.. code-block:: bash

    --model SYMPHONIE       # name of the SYMPHONIE folder
    --from GOT_REF2         # from this model
    --to GOT_REF5           # to this model


This command automatically creates a new simulation setup (``GOT_REF5``) cloned from the existing one (``GOT_REF2``), updating all relevant configuration references.


For example, if your folder tree is organized like this:

.. code-block:: bash

    ├── GOT271
    │   ├── GOT_REF2
    │   │   ├── BATHYMASK
    │   │   ├── GRAPHIQUES
    │   │   ├── LIST
    │   │   ├── NOTEBOOK
    │   │   ├── OFFLINE
    │   │   ├── RIVERS
    │   │   └── TIDES
    │   ├── GOT_REF3
    │   ├── GOT_REF5
    │   └── SYMPHONIE
    │       ├── CDIR_GFORTRAN
    │       ├── CDIR_IFORT
    │       ├── configbox
    │       ├── RDIR
    │       ├── SOURCES
    │       └── UDIR

So, in this example, inside the ``GOT271`` folder you have the list of simulations (``GOT_REF2``, ``GOT_REF3``, ...) and the ``SYMPHONIE`` model.  

Please run the command from the ``GOT271`` folder.

