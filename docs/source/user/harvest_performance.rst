=============================
Harvest Performance Benchmark
=============================

Reference throughput observed for Harvest in a real-world load. Use it to estimate how long a
large load will take. See :doc:`/user/load1` for how to run Harvest.


Real-World Load: On-Prem, NFS-Mounted Data
******************************************

A tenant loaded its archive into the Registry using Harvest, reading PDS4 products from an
on-premises, NFS-mounted file system.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Metric
     - Observed
   * - Harvest version
     - 5.1.3
   * - Products harvested
     - ~200,000
   * - Total elapsed time
     - ~17 hours
   * - Data source
     - On-premises, NFS-mounted storage
   * - Approximate throughput
     - ~12,000 products per hour (~3 products per second)
   * - Approximate time per product
     - ~0.3 seconds

Throughput is derived from the totals above and is approximate.


Estimating Your Load Time
*************************

As a rough guide, scale linearly from the throughput above:

.. code:: bash

   PRODUCT_COUNT=200000
   PRODUCTS_PER_HOUR=12000
   echo "scale=1; ${PRODUCT_COUNT} / ${PRODUCTS_PER_HOUR}" | bc

The result is the estimated number of hours. Actual time depends on your environment.

.. note::
   This is a single observation from one load, not a guaranteed rate. Elapsed time can vary
   with factors such as storage latency (NFS in this case), network conditions between
   Harvest and the Registry, and the size and type of the products being loaded.


Planning Large Loads
********************

- Expect a load of this size to run for many hours; run it in a persistent session (for example
  ``screen`` or ``tmux``) or as a background job so it is not interrupted by a closed terminal.
- Loading in smaller batches using multiple directories or a file manifest lets you
  verify results incrementally. See :doc:`/user/harvest_job_configuration`.
- Loaded data may take up to a few hours to become visible after Harvest completes, due to
  indexation delays.
