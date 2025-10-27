Ultility 3: Setup an ensemble run
=================================
This example demonstrates how to setup an ensemble run

Code Example
------------

This function has been **embedded into the GINCCO_lib** package and can now be executed directly through the command-line interface.

To use it, simply navigate to the directory that contains your list of SYMPHONIE simulations and run:


.. code-block:: bash

    gincco create-ensemble --rdir /tmpdir/tungnd/GOT271/SYMPHONIE/RDIR --simu GOTEN_NOTIDE --n 10


With: 

.. code-block:: bash

    --rdir /tmpdir/tungnd/GOT271/SYMPHONIE/RDIR         # RDIR folder path
    --simu GOTEN_NOTIDE                                 # base simulation to clone ensemble
    --n 10                                              # number of members




