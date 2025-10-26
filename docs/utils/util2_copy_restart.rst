Ultility 2: Save all restart files
==================================
This example demonstrates how to save all restart files

Code Example
------------

Create a new file called ``save_restart.py``



.. code-block:: python 

    #!/usr/bin/env python3
    """
    Monitor and save SYMPHONIE restart files automatically.
    Reads parameters from input.txt in the same folder.
    """

    import os
    import time
    import glob
    import shutil
    import logging
    from datetime import datetime, timedelta
    from netCDF4 import Dataset


    # ---------------------------------------------------
    # Read input parameters
    # ---------------------------------------------------
    def read_input_file(filename="input.txt"):
        params = {}
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    params[key.strip()] = val.strip()
        return params


    # ---------------------------------------------------
    # Copy restart files
    # ---------------------------------------------------
    def copy_restart_files(src_dir, dst_dir):
        if not os.path.exists(src_dir):
            logging.warning("Restart source folder not found: %s", src_dir)
            return
        os.makedirs(dst_dir, exist_ok=True)
        for fname in os.listdir(src_dir):
            src = os.path.join(src_dir, fname)
            dst = os.path.join(dst_dir, fname)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
        logging.info("Copied restart files from %s → %s", src_dir, dst_dir)


    # ---------------------------------------------------
    # Wait for OFFLINE file
    # ---------------------------------------------------
    def wait_for_offline_file(path, simu, date_check, wait_interval=300, max_tries=30):
        tries = 0
        while tries < max_tries:
            nc_files = glob.glob(f"{path}/{simu}/OFFLINE/{date_check.strftime('%Y%m%d')}*")
            if nc_files:
                return nc_files[0]
            logging.info("OFFLINE file for %s not found. Waiting %d sec...", date_check.strftime('%Y%m%d'), wait_interval)
            time.sleep(wait_interval)
            tries += 1
        return None


    # ---------------------------------------------------
    # Main routine
    # ---------------------------------------------------
    def main():
        cfg = read_input_file("input.txt")

        path = cfg.get("path", ".")
        model = cfg.get("model", "SYMPHONIE")
        simu = cfg.get("simu", "GOTEN_NOTIDE")
        tstart = datetime.fromisoformat(cfg.get("tstart", "2010-03-02"))
        tend = datetime.fromisoformat(cfg.get("tend", "2017-01-31"))
        restart_interval = int(cfg.get("restart_interval", 30))
        est_time = int(cfg.get("est_time", 600))
        max_tries = int(cfg.get("max_tries", 30))
        log_file = cfg.get("log_file", "save_restart.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(log_file, mode='a'), logging.StreamHandler()]
        )

        logging.info("=== SYMPHONIE Restart Monitor Started ===")
        logging.info("Simulation: %s | Model: %s | Path: %s", simu, model, path)

        duration_days = (tend - tstart).days
        tnow = tstart + timedelta(days=restart_interval)

        restart_target_root = os.path.join(path, model, "RDIR", simu, "restart_save")
        os.makedirs(restart_target_root, exist_ok=True)

        logging.info("Waiting %.1f minutes for first restart...", est_time / 60)
        time.sleep(est_time)

        i = 0
        rs_index = 0

        while i < duration_days - restart_interval:
            logging.info("Checking restart #%d for date %s", rs_index + 1, tnow.strftime('%Y-%m-%d'))
            ncfile = wait_for_offline_file(path, simu, tnow, max_tries=max_tries)
            if not ncfile:
                logging.error("File for %s not found after retries. Stopping.", tnow.strftime('%Y%m%d'))
                break

            restart_source = os.path.join(
                path, model, "RDIR", simu,
                "restart_outbis" if rs_index % 2 == 0 else "restart_output"
            )
            restart_target = os.path.join(restart_target_root, tnow.strftime('%Y%m%d'))
            copy_restart_files(restart_source, restart_target)

            # Move forward
            i += restart_interval
            tnow += timedelta(days=restart_interval)
            rs_index += 1

            logging.info("Restart saved. Waiting %.1f minutes for next cycle...", est_time / 60)
            time.sleep(est_time)

        logging.info("Finished all restart loops. Total restarts: %d", rs_index)
        logging.info("=== Finished ===")


    if __name__ == "__main__":
        main()


Then, create another file called input.txt

.. code-block:: bash

    path=/tmpdir/duytung/S271
    model=SYMPHONIE
    simu=GOTEN_NOTIDE
    tstart=2010-03-02
    tend=2017-01-31
    restart_interval=30
    est_time=600
    max_tries=30
    log_file=save_restart.log


Then, to run, just: 

.. code-block:: python

    python save_restart.py







