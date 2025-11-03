========================
Integration Testing Guide
========================

Overview
========

The PDS Registry uses Postman collections for automated integration testing. These tests verify that the full technology stack (OpenSearch, Registry API, data loading) works correctly and meets specific requirements.

**Tests run automatically:**

* On every feature branch update (via GitHub Actions)
* Daily on the ``main`` branch (via automated CI/CD)
* On stable release builds (with reports published alongside releases)

Prerequisites
=============

For Running Tests Manually
---------------------------

* `Postman Desktop Application <https://learning.postman.com/docs/getting-started/installation/installation-and-updates/>`_
* Docker and Docker Compose
* (Optional) TestRail credentials for validating test reporting

For Adding New Tests
---------------------

All of the above, plus:

* Access to `TestRail <https://cae-testrail.jpl.nasa.gov/testrail/>`_
* Familiarity with the `registry-ref-data <https://github.com/NASA-PDS/registry-ref-data>`_ repository

Running Tests Manually
=======================

Quick Start
-----------

1. **Clone the repository**

   .. code-block:: bash

      git clone https://github.com/NASA-PDS/registry.git
      cd registry

2. **Generate certificates** (first time only)

   .. code-block:: bash

      cd docker/certs
      ./generate-certs.sh
      cd ..

3. **Deploy the registry with test data**

   .. code-block:: bash

      docker compose --profile=int-registry-batch-loader up

   This will:

   * Start OpenSearch/Elasticsearch
   * Deploy the Registry API
   * Load test data using the registry-loader
   * Run the Postman integration tests automatically

4. **View test results** in the console output

5. **Clean up**

   .. code-block:: bash

      docker compose --profile=int-registry-batch-loader down --volume

Running Tests in Postman UI
----------------------------

To manually run or debug tests in Postman:

1. **Import the collection**

   * Open Postman
   * File → Import
   * Select ``docker/postman/postman_collection.json``

2. **Configure the environment**

   * Create a new environment or use an existing one
   * Set the ``baseUrl`` variable to your API endpoint

     * For local Docker: ``https://localhost:8443/api/search/``
     * For other environments: ``https://<host>:<port>/api/search/``

3. **Run the collection**

   * Click the "..." menu next to the collection name
   * Select "Run collection"
   * Review results in the Collection Runner

4. **Run individual requests**

   * Select a specific request
   * Click "Send"
   * View results in the "Test Results" tab

Adding New Tests
================

When to Add Tests
-----------------

Add integration tests for:

* New requirements or feature implementations
* Bug fixes that should be regression-tested
* Public-facing API examples (from the `user's manual <https://nasa-pds.github.io/pds-api/guides/search/tutorials.html>`_)

**Find issues needing tests:** Use this GitHub filter on registry-related repos:

.. code-block:: text

   is:issue is:closed label:requirement -label:i&t.skip

Test Addition Process
---------------------

Adding a new test involves updates to **three components:**

1. Reference datasets (if needed)
2. TestRail test case
3. Postman collection

Step-by-Step Guide
==================

1. Update Reference Datasets (Optional)
----------------------------------------

If your test requires new or modified data:

1. Update test datasets in the `registry-ref-data <https://github.com/NASA-PDS/registry-ref-data>`_ repository
2. Follow the instructions in that repository for adding/modifying datasets
3. After updating, restart your local deployment to load the new data:

   .. code-block:: bash

      docker compose --profile=int-registry-batch-loader down --volume
      docker compose --profile=int-registry-batch-loader up

2. Add Test Case in TestRail
-----------------------------

1. Navigate to the `Registry Requirements test suite <https://cae-testrail.jpl.nasa.gov/testrail/index.php?/suites/view/24324&group_by=cases:section_id&group_order=asc>`_
2. Create a new test case:

   * **Name:** Use the requirement title from GitHub (e.g., "As a user, I want to filter results by date")
   * **External link:** Add the GitHub issue URL (e.g., ``https://github.com/NASA-PDS/pds-api/issues/239``)

3. Save the test case and **record the test case ID** (e.g., ``C2555740``)

   * You'll need this ID for the Postman test assertions

3. Add Test in Postman
----------------------

1. **Deploy the registry** (if not already running)

   .. code-block:: bash

      cd docker
      docker compose --profile=int-registry-batch-loader up

2. **Open Postman** and import the collection (if not already imported)

3. **Create a new request** in the collection:

   * **Name:** Use the GitHub issue reference (e.g., ``NASA-PDS/pds-api#239``) or cookbook example name
   * **Method:** GET, POST, etc., as appropriate
   * **URL:** Use ``{{baseUrl}}`` variable + endpoint path

     * Example: ``{{baseUrl}}products?q=*:*``

4. **Configure request parameters:**

   * Path parameters
   * Query parameters
   * Headers
   * Body (for POST/PUT requests)

5. **Write test assertions** in the "Tests" tab:

   **CRITICAL:** Each assertion must include the TestRail test case ID in the test name.

   Example test code:

   .. code-block:: javascript

      pm.test("C2555740 the header Content-Type is application/json", () => {
          pm.response.to.have.header("Content-Type");
          pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
      });

      pm.test("C2555740 response status is 200", () => {
          pm.response.to.have.status(200);
      });

      pm.test("C2555740 response contains summary", () => {
          const jsonData = pm.response.json();
          pm.expect(jsonData).to.have.property('summary');
      });

   **Test Naming Convention:** ``C<TestRailID> <assertion description>``

   * This links Postman results to TestRail for automated reporting

6. **Test your request:**

   * Click "Send"
   * Verify the response in the "Body" tab
   * Check test results in the "Test Results" tab
   * **Save frequently!**

4. Validate the Full Suite
---------------------------

Before submitting your changes:

1. **Run the entire collection** in Postman:

   * Click "..." next to the collection name
   * Select "Run collection"
   * Verify all tests pass (including your new test)

2. **Run via Docker** (recommended):

   .. code-block:: bash

      docker compose --profile=int-registry-batch-loader down --volume
      docker compose --profile=int-registry-batch-loader up

   * Verify all tests pass in the console output

5. Export and Commit Changes
-----------------------------

1. **Export the collection** from Postman:

   * Click "..." next to the collection name
   * Select "Export"
   * Choose "Collection v2.1" format
   * Save to ``docker/postman/postman_collection.json`` (replace existing file)

2. **Create a branch and commit:**

   .. code-block:: bash

      git checkout -b test/add-api-239-test
      git add docker/postman/postman_collection.json
      git commit -m "Add integration test for NASA-PDS/pds-api#239"

3. **Create a Pull Request:**

   * Push your branch to GitHub
   * Create a PR with a description of the test added
   * Link to the original requirement/bug issue

6. Validate TestRail Reporting (Optional)
------------------------------------------

To verify that TestRail reporting works with your new test:

1. **Get TestRail API credentials:**

   * Follow steps in `TestRail API Reference <https://support.gurock.com/hc/en-us/articles/7077935859220-Accessing-the-TestRail-API>`_
   * Your username is your TestRail email address

2. **Set environment variables:**

   .. code-block:: bash

      export TESTRAIL_USERNAME="your-email@jpl.nasa.gov"
      export TESTRAIL_APIKEY="your-api-key"

3. **Run tests with TestRail reporting:**

   .. code-block:: bash

      cd docker
      docker compose --profile=testrail-reporting up

4. **Verify results** appear in TestRail under the appropriate test run

Postman Test Writing Tips
==========================

Common Assertions
-----------------

.. code-block:: javascript

   // Status code
   pm.test("C1234567 status code is 200", () => {
       pm.response.to.have.status(200);
   });

   // Response time
   pm.test("C1234567 response time is less than 2000ms", () => {
       pm.expect(pm.response.responseTime).to.be.below(2000);
   });

   // Header checks
   pm.test("C1234567 has correct content-type header", () => {
       pm.expect(pm.response.headers.get("Content-Type")).to.include("application/json");
   });

   // JSON structure
   pm.test("C1234567 response has required fields", () => {
       const jsonData = pm.response.json();
       pm.expect(jsonData).to.have.property('summary');
       pm.expect(jsonData).to.have.property('data');
   });

   // Array length
   pm.test("C1234567 returns at least one result", () => {
       const jsonData = pm.response.json();
       pm.expect(jsonData.data.length).to.be.above(0);
   });

   // Specific values
   pm.test("C1234567 product type is correct", () => {
       const jsonData = pm.response.json();
       pm.expect(jsonData.data[0].type).to.equal("Product_Observational");
   });

Using Environment Variables
----------------------------

.. code-block:: javascript

   // Access baseUrl
   const baseUrl = pm.environment.get("baseUrl");

   // Set variables for use in other requests
   pm.environment.set("productId", pm.response.json().data[0].id);

   // Use in subsequent requests
   {{productId}}

Docker Compose Profiles
========================

The registry repository includes several Docker Compose profiles for different testing scenarios:

+--------------------------------+-----------------------------------------------+----------------------------------------------+
| Profile                        | Use Case                                      | Components                                   |
+================================+===============================================+==============================================+
| ``dev-api``                    | API development with test data, no API        | OpenSearch + test data                       |
|                                | container                                     |                                              |
+--------------------------------+-----------------------------------------------+----------------------------------------------+
| ``pds-core-registry``          | Full stack with API                           | OpenSearch + Registry API                    |
+--------------------------------+-----------------------------------------------+----------------------------------------------+
| ``int-registry-batch-loader``  | **Integration testing**                       | Full stack + test data + Postman tests       |
+--------------------------------+-----------------------------------------------+----------------------------------------------+
| ``int-registry-service-loader``| Integration testing with service loader       | Full stack + service loader + tests          |
+--------------------------------+-----------------------------------------------+----------------------------------------------+
| ``testrail-reporting``         | TestRail report validation                    | Runs tests + pushes results to TestRail      |
+--------------------------------+-----------------------------------------------+----------------------------------------------+

Troubleshooting
===============

Tests Fail Locally But Pass in CI
----------------------------------

* Ensure you're using the same Docker image versions (check ``docker/.env``)
* Verify test data is current (``docker compose down --volume`` then restart)
* Check for timing issues (tests may need longer timeouts)

TestRail IDs Not Matching
--------------------------

* Verify the test case exists in TestRail
* Ensure the ID format is exactly ``C<number>`` at the start of the test name
* Check that the test is in the correct test suite

Collection Export Issues
-------------------------

* Always export in Collection v2.1 format
* Ensure you're replacing the entire file (not appending)
* Verify the JSON is valid before committing

Docker Compose Hangs
---------------------

* Check Docker logs: ``docker compose logs -f``
* Ensure ports 8443, 8080, 9200 are available
* Try cleaning up: ``docker compose down --volume`` and restart

Additional Resources
====================

* `Postman Learning Center <https://learning.postman.com/>`_
* `Registry API Documentation <https://nasa-pds.github.io/pds-api/>`_
* `Registry Ref Data Repository <https://github.com/NASA-PDS/registry-ref-data>`_
* `Docker Compose Documentation <https://github.com/NASA-PDS/registry/blob/main/docker/README.md>`_
* `TestRail Documentation <https://support.gurock.com/hc/en-us/categories/7077638315540-TestRail-Documentation>`_

Questions or Issues?
====================

* For test-related questions, open an issue in the `registry repository <https://github.com/NASA-PDS/registry/issues>`_
* For TestRail access issues, contact your PDS Engineering Node lead
* For general PDS questions, see the :doc:`../support/support`
