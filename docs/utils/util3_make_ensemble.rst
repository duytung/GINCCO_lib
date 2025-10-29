Ultility 3: Setup an ensemble run
=================================
This example demonstrates how to setup an ensemble run. 

Code Example
------------

This function has been **embedded into the GINCCO_lib** package and can now be executed directly through the command-line interface.

For example, if your folder tree look like this: 

.. code-block:: bash

    S271
    ├── GOTEN
    │     ├── BATHYMASK
    │     ├── GRAPHIQUES
    │     ├── LIST
    │     ├── NOTEBOOK
    │     ├── OFFLINE
    │     ├── PERTURB       # Create and go inside this folder to run the script
    │     ├── RIVERS
    │     ├── SOURCES
    │     └── TIDES
    ├── SYMPHONIE
    │     ├── CDIR_GFORTRAN
    │     ├── CDIR_IFORT
    │     ├── configbox
    │     ├── RDIR
    │     ├── SOURCES
    │     └── UDIR

In this case, create and navigate to the ``PERTURB`` folder and run:


.. code-block:: bash

    gincco create-ensemble --rdir /tmpdir/tungnd/GOT271/SYMPHONIE/RDIR --simu GOTEN_NOTIDE --n 10


With: 

.. code-block:: bash

    --rdir /tmpdir/tungnd/GOT271/SYMPHONIE/RDIR         # RDIR folder path
    --simu GOTEN_NOTIDE                                 # base simulation to clone ensemble
    --n 10                                              # number of members


After that, the ``PERTURB`` folder will have the structure like this: 

.. code-block:: bash


    PERTURB
    ├── 5.dir
    │     ├── FES2012
    │     ├── GRAPHIQUES
    │     ├── NOTEBOOK
    │     ├── OFFLINE
    │     ├── restart_input -> /tmpdir/duytung/S271/SYMPHONIE/RDIR/GOTEN//restart_ens
    │     ├── restart_iobess
    │     ├── restart_outbis
    │     ├── restart_output
    │     └── tmp
    ├── 6.dir
    │     ├── FES2012
    │     ├── GRAPHIQUES
    │     ├── NOTEBOOK
    │     ├── OFFLINE
    │     ├── restart_input -> /tmpdir/duytung/S271/SYMPHONIE/RDIR/GOTEN//restart_ens
    │     ├── restart_iobess
    │     ├── restart_outbis
    │     ├── restart_output
    │     └── tmp
    ├── 7.dir
    ├── 8.dir
    ├── 9.dir
    └── ...


So, now, inside the PERTURB, we will have several folders, each correspond to a member of the ensemble. 
In each folder, we will have ``NOTEBOOK`` folder to customize the member configuration, as well as ``OFFLINE`` and ``GRAPHIQUES`` folder to save the model output. 











