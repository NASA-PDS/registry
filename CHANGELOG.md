# Changelog

## [«unknown»](https://github.com/NASA-PDS/registry/tree/«unknown») (2025-04-24)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.3.1...«unknown»)

**Requirements:**

- As a user, I want to have read-only access to all registry indexes [\#350](https://github.com/NASA-PDS/registry/issues/350)
- As a data manager, I want to query OpenSearch Serverless from the command-line [\#273](https://github.com/NASA-PDS/registry/issues/273) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]

**Improvements:**

- Document the refresh rate of OpenSearch [\#361](https://github.com/NASA-PDS/registry/issues/361)
- Recreate PDS EN Registry from scratch and load only necessary data [\#352](https://github.com/NASA-PDS/registry/issues/352)
- Migrate registry-harvest-service documentation [\#78](https://github.com/NASA-PDS/registry/issues/78)

**Defects:**

- Registry return authorization error for ATM node [\#369](https://github.com/NASA-PDS/registry/issues/369) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- Update terraform to use port 443 not port 80 [\#365](https://github.com/NASA-PDS/registry/issues/365) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- Data products duplicated across en-registry and other node registries [\#351](https://github.com/NASA-PDS/registry/issues/351) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- Getting "blocked by: maximum OCU capacity reached" errors when harvesting [\#340](https://github.com/NASA-PDS/registry/issues/340) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- SBN user no longer able to access test registry [\#336](https://github.com/NASA-PDS/registry/issues/336) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- GEO index does not work, appears to be corrupted [\#331](https://github.com/NASA-PDS/registry/issues/331) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- AOSS 500/502 responses repeatedly observed under heavy load [\#329](https://github.com/NASA-PDS/registry/issues/329) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- Secret detection is broken on branch titan\_treks\_utility\_script [\#292](https://github.com/NASA-PDS/registry/issues/292) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- harvest created archive\_status as an array and registry-mgr updates it as a string [\#276](https://github.com/NASA-PDS/registry/issues/276) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- Missing NAIF from Legacy Dashboard [\#234](https://github.com/NASA-PDS/registry/issues/234) [[s.low](https://github.com/NASA-PDS/registry/labels/s.low)]

**Other closed issues:**

- Clean test suite to un-skip test skipped after multitenant migration [\#378](https://github.com/NASA-PDS/registry/issues/378)
- Respond to Registry SIA review from SAs [\#364](https://github.com/NASA-PDS/registry/issues/364)
- Complete security vulnerability assessment for registry [\#356](https://github.com/NASA-PDS/registry/issues/356)
- Update Registry configuration to support issues with IMG user\(s\) [\#337](https://github.com/NASA-PDS/registry/issues/337) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- Document in the wiki how the authorization on opensearch are managed [\#334](https://github.com/NASA-PDS/registry/issues/334)
- Reindex MCP Prod ATM registry index with corrected mappings [\#339](https://github.com/NASA-PDS/registry/issues/339)
- Investigate what the number of property per discipline node was at migration time [\#332](https://github.com/NASA-PDS/registry/issues/332)
- Onboard Irma from ATM node [\#325](https://github.com/NASA-PDS/registry/issues/325)
- Add reference links to LOLA data [\#316](https://github.com/NASA-PDS/registry/issues/316)
- As an administrator of the registry, I don't want ENG operator loading data to have administration authorizations [\#309](https://github.com/NASA-PDS/registry/issues/309)
- Finalize Cognito configuration in production for the Registry [\#307](https://github.com/NASA-PDS/registry/issues/307)
- Add Lola PDS4 script [\#305](https://github.com/NASA-PDS/registry/issues/305)
- Propose options to integrate Trek footprints to PDS products [\#295](https://github.com/NASA-PDS/registry/issues/295)
- Generalize the treks util to all the Treks services [\#294](https://github.com/NASA-PDS/registry/issues/294)
- Make sure all the useful Treks links are used/referenced in the PDS4 LAbel [\#291](https://github.com/NASA-PDS/registry/issues/291)
- Load the GIS Treks products in a local registry [\#289](https://github.com/NASA-PDS/registry/issues/289)
- Meet with Treks, MMGIS and GEOSTAC to discuss the PDS GIS activity [\#287](https://github.com/NASA-PDS/registry/issues/287)
- Design/Develop the initial GIS demo  [\#286](https://github.com/NASA-PDS/registry/issues/286)
- Create the PDS4 service labels for the dataset served by GIS services [\#285](https://github.com/NASA-PDS/registry/issues/285)
- Create GIS collection PDS4 label [\#284](https://github.com/NASA-PDS/registry/issues/284)
- Create context product unique identifier [\#283](https://github.com/NASA-PDS/registry/issues/283)
- Managed OpenSearch Snapshots [\#282](https://github.com/NASA-PDS/registry/issues/282)
- Migrate and fix types mismatches in registry mappings from all node cluster to OpenSearch serverless [\#280](https://github.com/NASA-PDS/registry/issues/280)
- Create snapshots of production OpenSearch clusters prior to shutdown [\#278](https://github.com/NASA-PDS/registry/issues/278)
- Copy data necessary for web mod efforts to search-en registry prior to shutdown [\#277](https://github.com/NASA-PDS/registry/issues/277)
- Deploy Multi-tenant Registry to test [\#272](https://github.com/NASA-PDS/registry/issues/272)
- Deploy Multi-tenant Registry to production and sync data [\#271](https://github.com/NASA-PDS/registry/issues/271)
- The migrated documents on opensearch serverless have a generated \_id [\#270](https://github.com/NASA-PDS/registry/issues/270)
- Upgrade docker compose as needed for the multitenant setup [\#269](https://github.com/NASA-PDS/registry/issues/269)
- Setup API Gateway - OpenSearch Serverless Authentication [\#256](https://github.com/NASA-PDS/registry/issues/256)
- Create Lambda Authorizer for Read Access - OpenSearch Serverless Authentication [\#255](https://github.com/NASA-PDS/registry/issues/255)
- Create Lambda Authorizer for Write Access - OpenSearch Serverless Authentication [\#254](https://github.com/NASA-PDS/registry/issues/254)
- Setup Cognito Identity Pool [\#253](https://github.com/NASA-PDS/registry/issues/253)
- Create IAM Roles for OpenSearch Serverless Authentication [\#252](https://github.com/NASA-PDS/registry/issues/252)
- Setup Cognito User Pool [\#251](https://github.com/NASA-PDS/registry/issues/251)
- Setup monitoring for Domain Notifications for all OpenSearch Domains in AWS [\#233](https://github.com/NASA-PDS/registry/issues/233)
- Registry-Sweepers Multiple Updates Statements Detected - NOT retry-related [\#225](https://github.com/NASA-PDS/registry/issues/225)
- Initial OpenSearch Serverless Setup and Deployment in MCP [\#223](https://github.com/NASA-PDS/registry/issues/223)
- Add registry costs to the PDS EN Cloud spreadsheet [\#218](https://github.com/NASA-PDS/registry/issues/218)
- Write a migration plan to multitenant registry [\#217](https://github.com/NASA-PDS/registry/issues/217)
- Design scalable, multi-tenant opensearch [\#212](https://github.com/NASA-PDS/registry/issues/212)
- B14.0 Update postman test suite with bug fixes for current build [\#201](https://github.com/NASA-PDS/registry/issues/201)
- B14.0 Update the postman test suite with all the requirement tests [\#200](https://github.com/NASA-PDS/registry/issues/200)
- Enable I&T to use and update registry-api automated tests [\#199](https://github.com/NASA-PDS/registry/issues/199)
- Design authorization handshake with Cognito, API Gateway, and Lambda for multi-tenancy approach [\#179](https://github.com/NASA-PDS/registry/issues/179)
- Revise documentation to be more clear about what is suitable for operational vs. development purposes [\#95](https://github.com/NASA-PDS/registry/issues/95)

## [v1.3.1](https://github.com/NASA-PDS/registry/tree/v1.3.1) (2023-11-16)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.3.0...v1.3.1)

**Requirements:**

- As a user, I want the registry to have 99.9999999% uptime [\#176](https://github.com/NASA-PDS/registry/issues/176)

**Other closed issues:**

- Assist with DUM infra setup in MCP [\#238](https://github.com/NASA-PDS/registry/issues/238)
- Write documentation and Training for Registry monitoring [\#224](https://github.com/NASA-PDS/registry/issues/224)
- Setup OIDC Authentication for MCP [\#222](https://github.com/NASA-PDS/registry/issues/222)

## [v1.3.0](https://github.com/NASA-PDS/registry/tree/v1.3.0) (2023-10-11)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.2.0...v1.3.0)

**Requirements:**

- As a system, I can support up to 25 simultaneous writes from Harvest [\#226](https://github.com/NASA-PDS/registry/issues/226)
- As an operator, I want to be notified of when Registry storage capacity exceeds 75% capacity. [\#211](https://github.com/NASA-PDS/registry/issues/211)
- As a manager, I want to see the progress of data sets ingested into registry vs. legacy registry [\#168](https://github.com/NASA-PDS/registry/issues/168)

**Defects:**

- Increase disk space for ATM opensearch [\#213](https://github.com/NASA-PDS/registry/issues/213) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- Provenance script failing on production registry [\#180](https://github.com/NASA-PDS/registry/issues/180) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]

**Other closed issues:**

- Improve test automation with postman [\#228](https://github.com/NASA-PDS/registry/issues/228)
- Fix lambda filters for registry-sweepers and registry-api [\#227](https://github.com/NASA-PDS/registry/issues/227)
- Create a new login for IMG Tariq [\#216](https://github.com/NASA-PDS/registry/issues/216)
- Use Richard's test dataset for the integrated postman tests in docker compose [\#198](https://github.com/NASA-PDS/registry/issues/198)
- incorporate registry-sweepers as dependency in the docker compose deployment script [\#197](https://github.com/NASA-PDS/registry/issues/197)
- Harvest OREX dataset from SBN-PSI web  [\#196](https://github.com/NASA-PDS/registry/issues/196)
- Add provenance script to the lucidchart AWS deployment diagram [\#195](https://github.com/NASA-PDS/registry/issues/195)
- Update cloud-front / ELB configuration to forward request headers to registry-api [\#191](https://github.com/NASA-PDS/registry/issues/191)
- Rework Registry+API Architecture Diagram in LucidChart [\#189](https://github.com/NASA-PDS/registry/issues/189)
- Run registry-manager to set all archive status to archived on all the collections for ATM and NAIF node [\#182](https://github.com/NASA-PDS/registry/issues/182)
- Add CloudWatch event for monitoring provenance script failure [\#167](https://github.com/NASA-PDS/registry/issues/167)

## [v1.2.0](https://github.com/NASA-PDS/registry/tree/v1.2.0) (2023-04-18)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.3...v1.2.0)

**Requirements:**

- As a user, I want to all metadata attributes to be searchable [\#153](https://github.com/NASA-PDS/registry/issues/153)
- As a user, I want to view dashboard report of bundles with archive status and other tracking information [\#130](https://github.com/NASA-PDS/registry/issues/130)
- Update documentation to include explicit example of how to query staged data [\#100](https://github.com/NASA-PDS/registry/issues/100)
- As a user, I want to indicate a product has been superseded [\#52](https://github.com/NASA-PDS/registry/issues/52)

**Improvements:**

- Update docs to be more clear that there is a required next step after data ingestion [\#139](https://github.com/NASA-PDS/registry/issues/139)

**Defects:**

- Expo system doesn't use latest images published to Docker Hub [\#175](https://github.com/NASA-PDS/registry/issues/175)
- ref\_collection\_lidvid field in some node registries populated using older versions of registry loader tools create string fields in the schema vs. the expected list types [\#159](https://github.com/NASA-PDS/registry/issues/159) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- TLS termination listening on wrong port [\#150](https://github.com/NASA-PDS/registry/issues/150) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- Expo Registry fails to start [\#149](https://github.com/NASA-PDS/registry/issues/149) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]
- OpenSearch service of Registry won't start on Linux [\#146](https://github.com/NASA-PDS/registry/issues/146) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- Harvest is throwing errors of "Forbidden index write" [\#132](https://github.com/NASA-PDS/registry/issues/132) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- registry-manager won't set archive-status on some collections [\#97](https://github.com/NASA-PDS/registry/issues/97) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]

**Other closed issues:**

- Update Terraform scripts to support multi-tenancy [\#188](https://github.com/NASA-PDS/registry/issues/188)
- Check that none of the Opensearch servers, besides NAIF have archive\_status==null [\#183](https://github.com/NASA-PDS/registry/issues/183)
- Add documentation on the auth.cfg file for the registry tools users [\#170](https://github.com/NASA-PDS/registry/issues/170)
- Schedule provenance script [\#160](https://github.com/NASA-PDS/registry/issues/160)
- Integrate new `provenance.py` script into operational deployment to tag products with Provenance information [\#141](https://github.com/NASA-PDS/registry/issues/141)
- Integrate new `provenance.py` script into integration tests to tag products with Provenance information [\#140](https://github.com/NASA-PDS/registry/issues/140)

## [v1.1.3](https://github.com/NASA-PDS/registry/tree/v1.1.3) (2022-12-14)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.2...v1.1.3)

**Defects:**

- follow on to \#118, registry-manager still unable to change archive status on bundle contents [\#136](https://github.com/NASA-PDS/registry/issues/136) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- archive status value was not changed on bundle's contents [\#118](https://github.com/NASA-PDS/registry/issues/118) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]

## [v1.1.2](https://github.com/NASA-PDS/registry/tree/v1.1.2) (2022-11-10)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.1...v1.1.2)

## [v1.1.1](https://github.com/NASA-PDS/registry/tree/v1.1.1) (2022-10-26)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.1.0...v1.1.1)

**Defects:**

- Continuous Delivery not working with OpenSearch [\#120](https://github.com/NASA-PDS/registry/issues/120) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]

## [v1.1.0](https://github.com/NASA-PDS/registry/tree/v1.1.0) (2022-09-21)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.2...v1.1.0)

**Defects:**

- Missing INSIGHT LDD v1600 [\#84](https://github.com/NASA-PDS/registry/issues/84) [[s.low](https://github.com/NASA-PDS/registry/labels/s.low)]

## [v1.0.2](https://github.com/NASA-PDS/registry/tree/v1.0.2) (2022-08-03)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.1...v1.0.2)

**Defects:**

- when docker compose starts, registry-api docker is missing curl [\#69](https://github.com/NASA-PDS/registry/issues/69) [[s.critical](https://github.com/NASA-PDS/registry/labels/s.critical)]
- Scalable Harvest does not replace file paths with the appropriate URL prefix [\#64](https://github.com/NASA-PDS/registry/issues/64) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- docker compose int-registry-batch-loader failure [\#41](https://github.com/NASA-PDS/registry/issues/41) [[s.medium](https://github.com/NASA-PDS/registry/labels/s.medium)]

**Other closed issues:**

- Update README to reflect best practices of other PDS repositories [\#53](https://github.com/NASA-PDS/registry/issues/53) [[s.high](https://github.com/NASA-PDS/registry/labels/s.high)]
- Develop script to update existing registry metadata per B12.1 metadata modifications [\#43](https://github.com/NASA-PDS/registry/issues/43)
- Plan and strategize how to migrate to OpenSearch deployments [\#54](https://github.com/NASA-PDS/registry/issues/54)
- Add supersede / update product version functionality in Registry Manager [\#56](https://github.com/NASA-PDS/registry/issues/56)
- Add new "alternate\_ids" field to Elasticsearch schema [\#59](https://github.com/NASA-PDS/registry/issues/59)
- Design the PDS4 definition for describing superseded LIDs via product metadata [\#57](https://github.com/NASA-PDS/registry/issues/57)

## [v1.0.1](https://github.com/NASA-PDS/registry/tree/v1.0.1) (2022-05-03)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.0...v1.0.1)

## [v1.0.0](https://github.com/NASA-PDS/registry/tree/v1.0.0) (2022-05-03)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/v1.0.0-SNAPSHOT...v1.0.0)

**Requirements:**

- Upgrade the initialization of the ES/OS database following latest upgrade of components [\#31](https://github.com/NASA-PDS/registry/issues/31)

## [v1.0.0-SNAPSHOT](https://github.com/NASA-PDS/registry/tree/v1.0.0-SNAPSHOT) (2022-01-20)

[Full Changelog](https://github.com/NASA-PDS/registry/compare/1f4d45e5a395b8d05b58a0924066dcd3cd0b3565...v1.0.0-SNAPSHOT)

**Requirements:**

- As a node operator, I want the the registry schema to update autonomously when new data is ingested. [\#113](https://github.com/NASA-PDS/registry/issues/113)
- As a developer, I want to include supplemental file data sizes in the registry [\#112](https://github.com/NASA-PDS/registry/issues/112)
- As a node operator, I want to ingest metadata regarding secondary collections that belong to a bundle. [\#109](https://github.com/NASA-PDS/registry/issues/109)
- As a node operator, I want to ingest metadata regarding secondary products that belong to a collection. [\#108](https://github.com/NASA-PDS/registry/issues/108)
- As a node operator, I want actionable, user-friendly error messages for registry schema failures [\#110](https://github.com/NASA-PDS/registry/issues/110)
- The service shall allow deletion of registered artifacts [\#103](https://github.com/NASA-PDS/registry/issues/103)
- The service shall provide a means identifying relationships between artifact registrations [\#104](https://github.com/NASA-PDS/registry/issues/104)
- As a registry user, I want to ingest supplemental metadata from Product\_Metadata\_Supplemental. [\#121](https://github.com/NASA-PDS/registry/issues/121)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
