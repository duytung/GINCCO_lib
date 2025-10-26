Ultility 1: Clone a simulation
==============================
This example demonstrates how to clone a simulation.

Code Example
------------

Create a new file called ``simulation_clone.sh`` and place it in the folder that contains the list of simulations.

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
The file ``simulation_clone.sh`` should be saved in the ``GOT271`` folder.

Here is the content of ``simulation_clone.sh``. 

.. code-block:: bash

   #!/usr/bin/env bash
   set -euo pipefail

   # === User settings ===
   model_name="SYMPHONIE"       # name of SYMPHONIE model
   ori="GOT_REF2"               # Copy from this folder
   new="GOT_REF5"               # To this folder
   path="$PWD"

   # === Sanity checks ===
   if [[ "$ori" == "$new" ]]; then
       echo "Duplicate simulation name: '$ori' == '$new'. Exiting..."
       exit 1
   fi

   if [[ ! -d "$model_name" ]]; then
       echo "Model directory '$model_name' not found. Exiting..."
       exit 1
   fi

   # === Create new configuration ===
   echo "Creating configuration directory..."
   (
       cd "$model_name"
       configbox/mkconfdir "$new"
   )

   # === Copy and replace content in UDIR ===
   echo "Copying UDIR..."
   cp -r "$model_name/UDIR/$ori" "$model_name/UDIR/$new"
   find "$model_name/UDIR/$new" -type f -exec sed -i "s|$ori|$new|g" {} +

   # === Copy and replace content in RDIR ===
   echo "Copying RDIR..."
   mkdir -p "$model_name/RDIR/$new"
   cp "$model_name/RDIR/$ori"/{s26*,submit*,note*,mask*} "$model_name/RDIR/$new" 2>/dev/null || true
   find "$model_name/RDIR/$new" -type f -exec sed -i "s|$ori|$new|g" {} +

   # === Prepare new simulation directory ===
   echo "Creating simulation directory structure..."
   mkdir -p "$new"/{OFFLINE,GRAPHIQUES,TIDES,LIST}

   for dir in RIVERS NOTEBOOK BATHYMASK LIST; do
       if [[ -d "$ori/$dir" ]]; then
           cp -r "$ori/$dir" "$new/"
       else
           echo "Warning: $dir not found in $ori"
       fi
   done

   # === Update NOTEBOOK references ===
   if [[ -d "$new/NOTEBOOK" ]]; then
       echo "Updating NOTEBOOK references..."
       find "$new/NOTEBOOK" -type f -exec sed -i "s|$ori|$new|g" {} +
   fi

   echo "Done. Created new simulation: '$new'"


Then, save the file. Then, run it by:

.. code-block:: bash

   . simulation_clone.sh


